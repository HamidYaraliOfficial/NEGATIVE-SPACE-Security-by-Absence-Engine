//! Privacy filter applied before any event leaves the host.
//! Fields configured under `[privacy] hash_fields` are salted+hashed;
//! fields under `drop_fields` are stripped entirely. Raw payload capture
//! is opt-in only and off by default.

use crate::config::PrivacySection;
use sha2::{Digest, Sha256};

pub struct PrivacyFilter {
    salt: String,
    hash_fields: Vec<String>,
    drop_fields: Vec<String>,
    pub collect_raw_payload: bool,
}

impl PrivacyFilter {
    pub fn new(cfg: &PrivacySection, host_salt: &str) -> Self {
        Self {
            salt: host_salt.to_string(),
            hash_fields: cfg.hash_fields.clone(),
            drop_fields: cfg.drop_fields.clone(),
            collect_raw_payload: cfg.collect_raw_payload,
        }
    }

    pub fn should_drop(&self, field: &str) -> bool {
        self.drop_fields.iter().any(|f| f == field)
    }

    pub fn should_hash(&self, field: &str) -> bool {
        self.hash_fields.iter().any(|f| f == field)
    }

    /// Deterministic salted hash - stable per host so correlation across
    /// events is still possible without exposing the raw value.
    pub fn hash_value(&self, value: &str) -> String {
        let mut hasher = Sha256::new();
        hasher.update(self.salt.as_bytes());
        hasher.update(b":");
        hasher.update(value.as_bytes());
        hex::encode(hasher.finalize())
    }

    /// Coarsens an IPv4 address to a /24 so relationship analysis is still
    /// possible without keeping a precise, potentially identifying address.
    pub fn coarsen_ipv4(&self, ip: &str) -> Option<String> {
        let parts: Vec<&str> = ip.split('.').collect();
        if parts.len() == 4 {
            Some(format!("{}.{}.{}.0/24", parts[0], parts[1], parts[2]))
        } else {
            None
        }
    }
}
