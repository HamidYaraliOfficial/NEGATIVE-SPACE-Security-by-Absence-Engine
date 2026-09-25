//! Collector layer. Each collector observes one class of host reality
//! (process lifecycle, network state, heartbeats) and emits canonical
//! events into the shared ring buffer.
//!
//! NOTE ON EBPF: this reference implementation uses portable polling
//! (`sysinfo`, `/proc`) so it builds and runs anywhere Rust runs. On
//! Linux with CAP_BPF and kernel >= 5.8, replace `process.rs` /
//! `network.rs` with an `aya`-based collector attached to
//! `sched_process_exec`, `sched_process_exit`, `tcp_connect` and
//! `inet_sock_set_state` tracepoints for true zero-poll, in-kernel
//! filtering. The `CanonicalEvent` contract in `models.rs` is the
//! stable seam between either implementation and the rest of the
//! agent/backend, so swapping the collector requires no changes
//! downstream. See `docs/ebpf-notes.md` in the repository root README.

pub mod heartbeat;
pub mod network;
pub mod process;

use crate::buffer::RingBuffer;
use crate::config::AgentConfig;
use crate::privacy::PrivacyFilter;
use std::sync::Arc;

#[derive(Clone)]
pub struct CollectorContext {
    pub cfg: Arc<AgentConfig>,
    pub buffer: Arc<RingBuffer>,
    pub privacy: Arc<PrivacyFilter>,
}
