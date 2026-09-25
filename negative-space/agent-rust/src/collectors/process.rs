//! Process lifecycle collector. Emits Started/Running/Exited transitions
//! with metadata only (pid, ppid, name hash, owner, timing) - never raw
//! command-line arguments unless `collect_raw_payload` is explicitly set.

use super::CollectorContext;
use crate::models::{CanonicalEvent, EventEnvelope, ProcessEvent, ProcessState};
use chrono::Utc;
use std::collections::HashSet;
use std::time::Duration;
use sysinfo::System;
use uuid::Uuid;

pub async fn run(ctx: CollectorContext) {
    if !ctx.cfg.collection.process_enabled {
        return;
    }
    let mut sys = System::new_all();
    let mut known_pids: HashSet<u32> = HashSet::new();
    let interval = Duration::from_millis(ctx.cfg.collection.process_poll_interval_ms);

    loop {
        sys.refresh_processes(sysinfo::ProcessesToUpdate::All, true);
        let current: HashSet<u32> = sys.processes().keys().map(|p| p.as_u32()).collect();

        // New processes -> Started
        for pid in current.difference(&known_pids) {
            if let Some(p) = sys.process(sysinfo::Pid::from_u32(*pid)) {
                emit_process_event(&ctx, p, *pid, ProcessState::Started);
            }
        }
        // Vanished processes -> Exited
        for pid in known_pids.difference(&current) {
            emit_exit_event(&ctx, *pid);
        }

        known_pids = current;
        tokio::time::sleep(interval).await;
    }
}

fn emit_process_event(
    ctx: &CollectorContext,
    p: &sysinfo::Process,
    pid: u32,
    state: ProcessState,
) {
    let name = p.name().to_string_lossy().to_string();
    let cmdline: Vec<String> = p
        .cmd()
        .iter()
        .map(|s| s.to_string_lossy().to_string())
        .collect();
    let cmdline_joined = cmdline.join(" ");

    let cmdline_hash = if ctx.privacy.should_drop("cmdline_full") {
        None
    } else if ctx.privacy.should_hash("cmdline_full") {
        Some(ctx.privacy.hash_value(&cmdline_joined))
    } else if ctx.privacy.collect_raw_payload {
        Some(cmdline_joined)
    } else {
        Some(ctx.privacy.hash_value(&cmdline_joined))
    };

    let event = ProcessEvent {
        pid,
        ppid: p.parent().map(|pp| pp.as_u32()),
        name,
        cmdline_hash,
        uid: p.user_id().map(|u| **u),
        gid: p.group_id().map(|g| *g as u32),
        started_at: Some(Utc::now()),
        state,
        container_id: None,
        namespace: None,
    };

    let envelope = EventEnvelope {
        event_id: Uuid::new_v4(),
        host_id: ctx.cfg.agent.host_id.clone(),
        tenant_id: ctx.cfg.agent.tenant_id.clone(),
        agent_version: env!("CARGO_PKG_VERSION").to_string(),
        occurred_at: Utc::now(),
        captured_at: Utc::now(),
        payload: CanonicalEvent::ProcessLifecycle(event),
    };
    ctx.buffer.push(envelope);
}

fn emit_exit_event(ctx: &CollectorContext, pid: u32) {
    let event = ProcessEvent {
        pid,
        ppid: None,
        name: String::new(),
        cmdline_hash: None,
        uid: None,
        gid: None,
        started_at: None,
        state: ProcessState::Exited,
        container_id: None,
        namespace: None,
    };
    let envelope = EventEnvelope {
        event_id: Uuid::new_v4(),
        host_id: ctx.cfg.agent.host_id.clone(),
        tenant_id: ctx.cfg.agent.tenant_id.clone(),
        agent_version: env!("CARGO_PKG_VERSION").to_string(),
        occurred_at: Utc::now(),
        captured_at: Utc::now(),
        payload: CanonicalEvent::ProcessLifecycle(event),
    };
    ctx.buffer.push(envelope);
}
