//! Network connection collector. Reads TCP socket state from /proc/net
//! on Linux (metadata only: ports, coarse remote address, state) and
//! degrades gracefully to a no-op on unsupported platforms.

use super::CollectorContext;
use crate::models::{CanonicalEvent, EventEnvelope, NetworkEvent};
use chrono::Utc;
use std::time::Duration;
use uuid::Uuid;

pub async fn run(ctx: CollectorContext) {
    if !ctx.cfg.collection.network_enabled {
        return;
    }
    let interval = Duration::from_millis(ctx.cfg.collection.network_poll_interval_ms);
    loop {
        for conn in read_tcp_connections() {
            emit_network_event(&ctx, conn);
        }
        tokio::time::sleep(interval).await;
    }
}

struct RawConn {
    local_port: u16,
    remote_ip: String,
    remote_port: u16,
    state: String,
}

#[cfg(target_os = "linux")]
fn read_tcp_connections() -> Vec<RawConn> {
    let mut out = Vec::new();
    if let Ok(content) = std::fs::read_to_string("/proc/net/tcp") {
        for line in content.lines().skip(1) {
            let fields: Vec<&str> = line.split_whitespace().collect();
            if fields.len() < 4 {
                continue;
            }
            if let (Some(local), Some(remote), Some(st)) =
                (fields.get(1), fields.get(2), fields.get(3))
            {
                if let (Some((lip, lport)), Some((rip, rport))) =
                    (parse_hex_addr(local), parse_hex_addr(remote))
                {
                    let _ = lip; // local IP intentionally not retained
                    out.push(RawConn {
                        local_port: lport,
                        remote_ip: rip,
                        remote_port: rport,
                        state: tcp_state_name(st),
                    });
                }
            }
        }
    }
    out
}

#[cfg(not(target_os = "linux"))]
fn read_tcp_connections() -> Vec<RawConn> {
    Vec::new()
}

#[cfg(target_os = "linux")]
fn parse_hex_addr(s: &str) -> Option<(String, u16)> {
    let parts: Vec<&str> = s.split(':').collect();
    if parts.len() != 2 {
        return None;
    }
    let ip_hex = parts[0];
    let port = u16::from_str_radix(parts[1], 16).ok()?;
    if ip_hex.len() != 8 {
        return None;
    }
    let bytes = u32::from_str_radix(ip_hex, 16).ok()?;
    let ip = format!(
        "{}.{}.{}.{}",
        bytes & 0xFF,
        (bytes >> 8) & 0xFF,
        (bytes >> 16) & 0xFF,
        (bytes >> 24) & 0xFF
    );
    Some((ip, port))
}

#[cfg(target_os = "linux")]
fn tcp_state_name(hex: &str) -> String {
    match hex {
        "01" => "ESTABLISHED",
        "02" => "SYN_SENT",
        "03" => "SYN_RECV",
        "04" => "FIN_WAIT1",
        "05" => "FIN_WAIT2",
        "06" => "TIME_WAIT",
        "07" => "CLOSE",
        "08" => "CLOSE_WAIT",
        "0A" => "LISTEN",
        _ => "UNKNOWN",
    }
    .to_string()
}

fn emit_network_event(ctx: &CollectorContext, conn: RawConn) {
    let remote_ip_hash = if ctx.privacy.should_drop("remote_ip") {
        None
    } else if ctx.privacy.should_hash("remote_ip") {
        Some(ctx.privacy.hash_value(&conn.remote_ip))
    } else {
        None
    };
    let remote_ip_prefix = ctx.privacy.coarsen_ipv4(&conn.remote_ip);

    let event = NetworkEvent {
        local_port: conn.local_port,
        remote_port: Some(conn.remote_port),
        remote_ip_hash,
        remote_ip_prefix,
        protocol: "tcp".to_string(),
        state: conn.state,
        pid: None,
        direction: if conn.local_port < 1024 { "inbound".into() } else { "outbound".into() },
    };
    let envelope = EventEnvelope {
        event_id: Uuid::new_v4(),
        host_id: ctx.cfg.agent.host_id.clone(),
        tenant_id: ctx.cfg.agent.tenant_id.clone(),
        agent_version: env!("CARGO_PKG_VERSION").to_string(),
        occurred_at: Utc::now(),
        captured_at: Utc::now(),
        payload: CanonicalEvent::NetworkConnection(event),
    };
    ctx.buffer.push(envelope);
}
