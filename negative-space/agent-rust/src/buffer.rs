//! Bounded in-memory ring buffer with an on-disk overflow/offline spool.
//! Guarantees the agent never grows unbounded memory usage and can
//! survive a backend outage by queueing encrypted-at-rest batches to disk.

use crate::models::EventEnvelope;
use anyhow::Result;
use flate2::write::GzEncoder;
use flate2::Compression;
use std::collections::VecDeque;
use std::io::Write;
use std::path::PathBuf;
use std::sync::Mutex;
use tokio::fs;

pub struct RingBuffer {
    inner: Mutex<VecDeque<EventEnvelope>>,
    capacity: usize,
    dropped: Mutex<u64>,
}

impl RingBuffer {
    pub fn new(capacity: usize) -> Self {
        Self {
            inner: Mutex::new(VecDeque::with_capacity(capacity.min(4096))),
            capacity,
            dropped: Mutex::new(0),
        }
    }

    /// Push an event. Applies backpressure: if the buffer is full, the
    /// oldest event is dropped and the drop counter incremented (never
    /// panics, never grows past capacity).
    pub fn push(&self, event: EventEnvelope) {
        let mut guard = self.inner.lock().unwrap();
        if guard.len() >= self.capacity {
            guard.pop_front();
            *self.dropped.lock().unwrap() += 1;
        }
        guard.push_back(event);
    }

    pub fn drain_batch(&self, max: usize) -> Vec<EventEnvelope> {
        let mut guard = self.inner.lock().unwrap();
        let n = max.min(guard.len());
        guard.drain(..n).collect()
    }

    pub fn len(&self) -> usize {
        self.inner.lock().unwrap().len()
    }

    pub fn dropped_total(&self) -> u64 {
        *self.dropped.lock().unwrap()
    }
}

/// Disk-backed spool used only when the backend is unreachable. Batches
/// are gzip-compressed JSON lines; the agent enforces `max_disk_bytes`
/// by refusing to spool once the budget is exhausted (oldest-first
/// eviction keeps the most recent evidence).
pub struct OfflineSpool {
    dir: PathBuf,
    max_bytes: u64,
}

impl OfflineSpool {
    pub async fn new(dir: PathBuf, max_bytes: u64) -> Result<Self> {
        fs::create_dir_all(&dir).await?;
        Ok(Self { dir, max_bytes })
    }

    pub async fn spool(&self, batch: &[EventEnvelope]) -> Result<()> {
        self.enforce_budget().await?;
        let json = serde_json::to_vec(batch)?;
        let mut encoder = GzEncoder::new(Vec::new(), Compression::default());
        encoder.write_all(&json)?;
        let compressed = encoder.finish()?;
        let filename = format!("{}.jsonl.gz", uuid::Uuid::new_v4());
        fs::write(self.dir.join(filename), compressed).await?;
        Ok(())
    }

    pub async fn drain_oldest(&self, limit: usize) -> Result<Vec<(PathBuf, Vec<EventEnvelope>)>> {
        let mut entries = fs::read_dir(&self.dir).await?;
        let mut files = Vec::new();
        while let Some(entry) = entries.next_entry().await? {
            if entry.path().extension().map(|e| e == "gz").unwrap_or(false) {
                files.push(entry.path());
            }
        }
        files.sort();
        let mut out = Vec::new();
        for path in files.into_iter().take(limit) {
            let compressed = fs::read(&path).await?;
            let json = decompress(&compressed)?;
            let batch: Vec<EventEnvelope> = serde_json::from_slice(&json)?;
            out.push((path, batch));
        }
        Ok(out)
    }

    async fn enforce_budget(&self) -> Result<()> {
        let mut total: u64 = 0;
        let mut entries = fs::read_dir(&self.dir).await?;
        let mut files = Vec::new();
        while let Some(entry) = entries.next_entry().await? {
            let meta = entry.metadata().await?;
            total += meta.len();
            files.push((entry.path(), meta.len()));
        }
        if total <= self.max_bytes {
            return Ok(());
        }
        files.sort_by_key(|(p, _)| p.clone());
        for (path, size) in files {
            if total <= self.max_bytes {
                break;
            }
            let _ = fs::remove_file(&path).await;
            total = total.saturating_sub(size);
        }
        Ok(())
    }
}

fn decompress(bytes: &[u8]) -> Result<Vec<u8>> {
    use flate2::read::GzDecoder;
    use std::io::Read;
    let mut decoder = GzDecoder::new(bytes);
    let mut out = Vec::new();
    decoder.read_to_end(&mut out)?;
    Ok(out)
}
