//! Configuration loading + validation. Secure-by-default: if the config
//! file is missing required fields, the agent refuses to start rather
//! than silently collecting with unsafe defaults.

use anyhow::{bail, Context, Result};
use serde::Deserialize;
use std::path::Path;

#[derive(Debug, Clone, Deserialize)]
pub struct AgentSection {
    #[serde(default)]
    pub host_id: String,
    pub tenant_id: String,
    #[serde(default = "default_env")]
    pub environment: String,
    #[serde(default)]
    pub tags: Vec<String>,
}

fn default_env() -> String {
    "production".to_string()
}

#[derive(Debug, Clone, Deserialize)]
pub struct BackendSection {
    pub url: String,
    pub enrollment_token: String,
    #[serde(default = "default_true")]
    pub verify_tls: bool,
    #[serde(default = "default_timeout")]
    pub timeout_seconds: u64,
}

fn default_true() -> bool {
    true
}
fn default_timeout() -> u64 {
    10
}

#[derive(Debug, Clone, Deserialize)]
pub struct CollectionSection {
    #[serde(default = "default_true")]
    pub process_enabled: bool,
    #[serde(default = "default_true")]
    pub network_enabled: bool,
    #[serde(default = "default_true")]
    pub heartbeat_enabled: bool,
    #[serde(default = "default_hb_interval")]
    pub heartbeat_interval_seconds: u64,
    #[serde(default = "default_poll")]
    pub process_poll_interval_ms: u64,
    #[serde(default = "default_poll")]
    pub network_poll_interval_ms: u64,
    #[serde(default = "default_sample_rate")]
    pub sample_rate: f32,
}

fn default_hb_interval() -> u64 {
    30
}
fn default_poll() -> u64 {
    2000
}
fn default_sample_rate() -> f32 {
    1.0
}

#[derive(Debug, Clone, Deserialize)]
pub struct BufferSection {
    #[serde(default = "default_max_mem_events")]
    pub max_memory_events: usize,
    #[serde(default = "default_max_disk")]
    pub max_disk_bytes: u64,
    pub spool_dir: String,
    #[serde(default = "default_batch_size")]
    pub batch_size: usize,
    #[serde(default = "default_flush_ms")]
    pub flush_interval_ms: u64,
    #[serde(default = "default_true")]
    pub compress: bool,
}

fn default_max_mem_events() -> usize {
    20000
}
fn default_max_disk() -> u64 {
    104_857_600
}
fn default_batch_size() -> usize {
    500
}
fn default_flush_ms() -> u64 {
    3000
}

#[derive(Debug, Clone, Deserialize, Default)]
pub struct PrivacySection {
    #[serde(default)]
    pub hash_fields: Vec<String>,
    #[serde(default)]
    pub drop_fields: Vec<String>,
    #[serde(default)]
    pub collect_raw_payload: bool,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ResourceGuardSection {
    #[serde(default = "default_max_cpu")]
    pub max_cpu_percent: f32,
    #[serde(default = "default_max_mem_mb")]
    pub max_memory_mb: f32,
    #[serde(default = "default_max_queue")]
    pub max_queue_events: u64,
    #[serde(default = "default_fail_mode")]
    pub fail_mode: String,
}

fn default_max_cpu() -> f32 {
    5.0
}
fn default_max_mem_mb() -> f32 {
    256.0
}
fn default_max_queue() -> u64 {
    50000
}
fn default_fail_mode() -> String {
    "fail_open".to_string()
}

#[derive(Debug, Clone, Deserialize)]
pub struct AgentConfig {
    pub agent: AgentSection,
    pub backend: BackendSection,
    pub collection: CollectionSection,
    pub buffer: BufferSection,
    #[serde(default)]
    pub privacy: PrivacySection,
    pub resource_guard: ResourceGuardSection,
}

impl AgentConfig {
    pub fn load(path: &Path) -> Result<Self> {
        let raw = std::fs::read_to_string(path)
            .with_context(|| format!("reading config at {}", path.display()))?;
        let mut cfg: AgentConfig = toml::from_str(&raw).context("parsing agent.toml")?;
        cfg.validate()?;
        if cfg.agent.host_id.trim().is_empty() {
            cfg.agent.host_id = uuid::Uuid::new_v4().to_string();
        }
        Ok(cfg)
    }

    fn validate(&self) -> Result<()> {
        if self.backend.url.trim().is_empty() {
            bail!("backend.url must be set");
        }
        if self.backend.enrollment_token.trim().is_empty() {
            bail!("backend.enrollment_token must be set - refusing to start with an unauthenticated agent");
        }
        if !(0.0..=1.0).contains(&self.collection.sample_rate) {
            bail!("collection.sample_rate must be between 0.0 and 1.0");
        }
        if self.resource_guard.fail_mode != "fail_open" && self.resource_guard.fail_mode != "fail_closed"
        {
            bail!("resource_guard.fail_mode must be 'fail_open' or 'fail_closed'");
        }
        Ok(())
    }
}
