//! Ships batches to the backend over HTTPS with retry + offline fallback.

use crate::buffer::{OfflineSpool, RingBuffer};
use crate::config::AgentConfig;
use crate::models::EventBatch;
use anyhow::Result;
use std::sync::Arc;
use std::time::Duration;
use tracing::{info, warn};

pub struct Shipper {
    client: reqwest::Client,
    backend_url: String,
    token: String,
    host_id: String,
    tenant_id: String,
}

impl Shipper {
    pub fn new(cfg: &AgentConfig) -> Result<Self> {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(cfg.backend.timeout_seconds))
            .danger_accept_invalid_certs(!cfg.backend.verify_tls)
            .build()?;
        Ok(Self {
            client,
            backend_url: cfg.backend.url.trim_end_matches('/').to_string(),
            token: cfg.backend.enrollment_token.clone(),
            host_id: cfg.agent.host_id.clone(),
            tenant_id: cfg.agent.tenant_id.clone(),
        })
    }

    pub async fn send_batch(&self, batch: &EventBatch) -> Result<bool> {
        let url = format!("{}/api/v1/ingest/events", self.backend_url);
        let resp = self
            .client
            .post(&url)
            .bearer_auth(&self.token)
            .json(batch)
            .send()
            .await;
        match resp {
            Ok(r) if r.status().is_success() => Ok(true),
            Ok(r) => {
                warn!(status = %r.status(), "backend rejected batch");
                Ok(false)
            }
            Err(e) => {
                warn!(error = %e, "backend unreachable");
                Ok(false)
            }
        }
    }

    pub fn new_batch(&self, events: Vec<crate::models::EventEnvelope>) -> EventBatch {
        EventBatch {
            host_id: self.host_id.clone(),
            tenant_id: self.tenant_id.clone(),
            events,
        }
    }
}

/// Background loop: drain ring buffer -> try live send -> spool on failure.
/// Also periodically retries anything already spooled to disk.
pub async fn run_shipping_loop(
    cfg: Arc<AgentConfig>,
    buffer: Arc<RingBuffer>,
    spool: Arc<OfflineSpool>,
    shipper: Arc<Shipper>,
) {
    let mut interval = tokio::time::interval(Duration::from_millis(cfg.buffer.flush_interval_ms));
    loop {
        interval.tick().await;

        // First, retry anything already spooled.
        if let Ok(spooled) = spool.drain_oldest(5).await {
            for (path, events) in spooled {
                let batch = shipper.new_batch(events);
                if shipper.send_batch(&batch).await.unwrap_or(false) {
                    let _ = tokio::fs::remove_file(&path).await;
                    info!("flushed spooled batch");
                }
            }
        }

        // Then ship fresh events.
        let events = buffer.drain_batch(cfg.buffer.batch_size);
        if events.is_empty() {
            continue;
        }
        let batch = shipper.new_batch(events.clone());
        match shipper.send_batch(&batch).await {
            Ok(true) => {}
            _ => {
                if let Err(e) = spool.spool(&events).await {
                    warn!(error = %e, "failed to spool events - dropping");
                }
            }
        }
    }
}
