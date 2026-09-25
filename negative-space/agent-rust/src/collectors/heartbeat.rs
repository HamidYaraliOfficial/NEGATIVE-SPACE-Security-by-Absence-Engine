//! Emits the agent's own heartbeat and self-health telemetry so the
//! backend's Collector Integrity Monitor can tell "agent is silent"
//! apart from "service is silent".

use super::CollectorContext;
use crate::models::{AgentHealthEvent, CanonicalEvent, EventEnvelope, HeartbeatEvent};
use chrono::Utc;
use std::time::Duration;
use sysinfo::System;
use uuid::Uuid;

pub async fn run(ctx: CollectorContext) {
    if !ctx.cfg.collection.heartbeat_enabled {
        return;
    }
    let interval = Duration::from_secs(ctx.cfg.collection.heartbeat_interval_seconds);
    let mut sys = System::new_all();
    let started = std::time::Instant::now();
    let mut seq: u64 = 0;

    loop {
        seq += 1;
        let hb = HeartbeatEvent {
            service_id: format!("agent:{}", ctx.cfg.agent.host_id),
            sequence: seq,
            uptime_seconds: started.elapsed().as_secs(),
        };
        push(&ctx, CanonicalEvent::Heartbeat(hb));

        sys.refresh_cpu_all();
        sys.refresh_memory();
        let health = AgentHealthEvent {
            cpu_percent: sys.global_cpu_usage(),
            memory_mb: (sys.used_memory() / 1024 / 1024) as f32,
            queue_depth: ctx.buffer.len() as u64,
            dropped_events_total: ctx.buffer.dropped_total(),
            spool_bytes: 0,
            collectors_ok: true,
        };
        push(&ctx, CanonicalEvent::AgentHealth(health));

        tokio::time::sleep(interval).await;
    }
}

fn push(ctx: &CollectorContext, payload: CanonicalEvent) {
    let envelope = EventEnvelope {
        event_id: Uuid::new_v4(),
        host_id: ctx.cfg.agent.host_id.clone(),
        tenant_id: ctx.cfg.agent.tenant_id.clone(),
        agent_version: env!("CARGO_PKG_VERSION").to_string(),
        occurred_at: Utc::now(),
        captured_at: Utc::now(),
        payload,
    };
    ctx.buffer.push(envelope);
}
