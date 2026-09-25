//! NEGATIVE SPACE host sensor entrypoint.
//! Wires config -> privacy filter -> ring buffer -> collectors -> shipper.

mod buffer;
mod collectors;
mod config;
mod models;
mod privacy;
mod shipper;

use anyhow::Result;
use buffer::{OfflineSpool, RingBuffer};
use clap::Parser;
use collectors::CollectorContext;
use config::AgentConfig;
use privacy::PrivacyFilter;
use shipper::{run_shipping_loop, Shipper};
use std::path::PathBuf;
use std::sync::Arc;
use tracing::info;
use tracing_subscriber::EnvFilter;

#[derive(Parser, Debug)]
#[command(name = "negspace-agent", version, about = "NEGATIVE SPACE host sensor")]
struct Cli {
    /// Path to agent.toml
    #[arg(short, long, default_value = "config/agent.toml")]
    config: PathBuf,
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env().add_directive("info".parse()?))
        .init();

    let cli = Cli::parse();
    let cfg = Arc::new(AgentConfig::load(&cli.config)?);
    info!(host_id = %cfg.agent.host_id, tenant = %cfg.agent.tenant_id, "negspace-agent starting");

    let privacy = Arc::new(PrivacyFilter::new(&cfg.privacy, &cfg.agent.host_id));
    let buffer = Arc::new(RingBuffer::new(cfg.buffer.max_memory_events));
    let spool = Arc::new(
        OfflineSpool::new(PathBuf::from(&cfg.buffer.spool_dir), cfg.buffer.max_disk_bytes).await?,
    );
    let shipper = Arc::new(Shipper::new(&cfg)?);

    let ctx = CollectorContext {
        cfg: cfg.clone(),
        buffer: buffer.clone(),
        privacy: privacy.clone(),
    };

    let mut handles = Vec::new();
    handles.push(tokio::spawn(collectors::process::run(ctx.clone())));
    handles.push(tokio::spawn(collectors::network::run(ctx.clone())));
    handles.push(tokio::spawn(collectors::heartbeat::run(ctx.clone())));
    handles.push(tokio::spawn(run_shipping_loop(
        cfg.clone(),
        buffer.clone(),
        spool.clone(),
        shipper.clone(),
    )));

    info!("all collectors + shipper running");
    for h in handles {
        let _ = h.await;
    }
    Ok(())
}
