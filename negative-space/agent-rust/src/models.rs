//! Canonical event models shipped from the host sensor to the backend.
//! These are intentionally metadata-only: no file contents, no packet
//! payloads, no command-line secrets in the clear (see `privacy.rs`).

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case", tag = "event_type")]
pub enum CanonicalEvent {
    ProcessLifecycle(ProcessEvent),
    NetworkConnection(NetworkEvent),
    Heartbeat(HeartbeatEvent),
    AgentHealth(AgentHealthEvent),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventEnvelope {
    pub event_id: Uuid,
    pub host_id: String,
    pub tenant_id: String,
    pub agent_version: String,
    /// Time the underlying kernel/OS event actually occurred, if known.
    pub occurred_at: DateTime<Utc>,
    /// Time the agent captured/serialized the event (used for clock-skew
    /// and provenance analysis on the backend).
    pub captured_at: DateTime<Utc>,
    #[serde(flatten)]
    pub payload: CanonicalEvent,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessEvent {
    pub pid: u32,
    pub ppid: Option<u32>,
    pub name: String,
    /// Hashed by default per `privacy.hash_fields`; never the raw argv.
    pub cmdline_hash: Option<String>,
    pub uid: Option<u32>,
    pub gid: Option<u32>,
    pub started_at: Option<DateTime<Utc>>,
    pub state: ProcessState,
    pub container_id: Option<String>,
    pub namespace: Option<String>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ProcessState {
    Started,
    Running,
    Exited,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkEvent {
    pub local_port: u16,
    pub remote_port: Option<u16>,
    /// Hashed unless the operator explicitly opts out (see privacy.rs).
    pub remote_ip_hash: Option<String>,
    pub remote_ip_prefix: Option<String>, // coarse /24 or /48, useful without being identifying
    pub protocol: String,                 // tcp | udp
    pub state: String,                    // ESTABLISHED, LISTEN, CLOSE_WAIT, ...
    pub pid: Option<u32>,
    pub direction: String,                // inbound | outbound
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HeartbeatEvent {
    pub service_id: String,
    pub sequence: u64,
    pub uptime_seconds: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentHealthEvent {
    pub cpu_percent: f32,
    pub memory_mb: f32,
    pub queue_depth: u64,
    pub dropped_events_total: u64,
    pub spool_bytes: u64,
    pub collectors_ok: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct EventBatch {
    pub host_id: String,
    pub tenant_id: String,
    pub events: Vec<EventEnvelope>,
}
