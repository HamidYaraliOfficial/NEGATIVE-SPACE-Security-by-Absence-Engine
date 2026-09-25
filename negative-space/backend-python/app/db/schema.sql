-- NEGATIVE SPACE — PostgreSQL schema (reference / docker-entrypoint bootstrap)
-- Designed for partitioning on high-volume tables (events) and heavy
-- indexing on the columns the Detection Engine filters on most.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(16) NOT NULL DEFAULT 'analyst',
    tenant_id VARCHAR(64) NOT NULL DEFAULT 'default',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(64) NOT NULL DEFAULT 'default',
    entity_type VARCHAR(32) NOT NULL,
    name VARCHAR(255) NOT NULL,
    criticality VARCHAR(16) NOT NULL DEFAULT 'medium',
    attributes JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(tenant_id, entity_type, name)
);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_tenant ON entities(tenant_id);

CREATE TABLE IF NOT EXISTS expected_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    signal_name VARCHAR(128) NOT NULL,
    expected_interval_seconds DOUBLE PRECISION NOT NULL,
    interval_stddev_seconds DOUBLE PRECISION NOT NULL DEFAULT 0,
    tolerance_multiplier DOUBLE PRECISION NOT NULL DEFAULT 2.5,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    context JSONB NOT NULL DEFAULT '{}',
    source VARCHAR(32) NOT NULL DEFAULT 'learned',
    version INT NOT NULL DEFAULT 1,
    status VARCHAR(16) NOT NULL DEFAULT 'active',
    explanation TEXT DEFAULT '',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_expected_signals_entity ON expected_signals(entity_id, signal_name);

CREATE TABLE IF NOT EXISTS observations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    signal_name VARCHAR(128) NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL,
    observed_count INT NOT NULL DEFAULT 0,
    last_interval_seconds DOUBLE PRECISION NOT NULL DEFAULT 0,
    UNIQUE(entity_id, signal_name)
);
CREATE INDEX IF NOT EXISTS idx_observations_last_seen ON observations(last_seen_at);

CREATE TABLE IF NOT EXISTS cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(64) NOT NULL DEFAULT 'default',
    title VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'open',
    priority VARCHAR(16) NOT NULL DEFAULT 'medium',
    owner VARCHAR(255) DEFAULT '',
    notes JSONB NOT NULL DEFAULT '[]',
    tags JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS detections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(64) NOT NULL DEFAULT 'default',
    entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    category VARCHAR(64) NOT NULL,
    level VARCHAR(16) NOT NULL,
    severity VARCHAR(16) NOT NULL DEFAULT 'medium',
    confidence DOUBLE PRECISION NOT NULL,
    silence_started_at TIMESTAMPTZ NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expected_summary TEXT NOT NULL,
    observed_summary TEXT NOT NULL,
    evidence JSONB NOT NULL DEFAULT '{}',
    baseline_version INT NOT NULL DEFAULT 1,
    status VARCHAR(16) NOT NULL DEFAULT 'open',
    review_verdict VARCHAR(32) DEFAULT '',
    case_id UUID REFERENCES cases(id)
);
CREATE INDEX IF NOT EXISTS idx_detections_entity ON detections(entity_id);
CREATE INDEX IF NOT EXISTS idx_detections_detected_at ON detections(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_detections_status ON detections(status);

CREATE TABLE IF NOT EXISTS relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(64) NOT NULL DEFAULT 'default',
    source_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    target_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relationship_type VARCHAR(64) NOT NULL,
    expected BOOLEAN NOT NULL DEFAULT TRUE,
    observed BOOLEAN NOT NULL DEFAULT TRUE,
    frequency_per_day DOUBLE PRECISION NOT NULL DEFAULT 0,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    last_observed_at TIMESTAMPTZ,
    first_learned_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_rel_source ON relationships(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_rel_target ON relationships(target_entity_id);

CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(64) NOT NULL DEFAULT 'default',
    title VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'open',
    risk_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    first_divergence_at TIMESTAMPTZ,
    recovered_at TIMESTAMPTZ,
    detection_ids JSONB NOT NULL DEFAULT '[]',
    timeline JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    host_id VARCHAR(128) UNIQUE NOT NULL,
    tenant_id VARCHAR(64) NOT NULL DEFAULT 'default',
    agent_version VARCHAR(32) DEFAULT '',
    last_seen_at TIMESTAMPTZ,
    cpu_percent DOUBLE PRECISION DEFAULT 0,
    memory_mb DOUBLE PRECISION DEFAULT 0,
    queue_depth INT DEFAULT 0,
    dropped_events_total INT DEFAULT 0,
    status VARCHAR(16) NOT NULL DEFAULT 'unknown',
    config JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_agents_last_seen ON agents(last_seen_at);

CREATE TABLE IF NOT EXISTS business_hours (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    tenant_id VARCHAR(64) NOT NULL DEFAULT 'default',
    name VARCHAR(255) NOT NULL,
    timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
    schedule JSONB NOT NULL DEFAULT '{}',
    is_maintenance_window BOOLEAN NOT NULL DEFAULT FALSE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(64) NOT NULL DEFAULT 'default',
    actor VARCHAR(255) NOT NULL,
    action VARCHAR(128) NOT NULL,
    target VARCHAR(255) DEFAULT '',
    details JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- High-volume raw event ledger, partitioned by month. Detection reads
-- mostly from `observations` (a compact rollup); this table is the
-- source of truth / evidence store for the Evidence Graph.
CREATE TABLE IF NOT EXISTS events (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(64) NOT NULL DEFAULT 'default',
    host_id VARCHAR(128) NOT NULL,
    entity_id UUID,
    event_type VARCHAR(64) NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    PRIMARY KEY (id, occurred_at)
) PARTITION BY RANGE (occurred_at);

-- Example initial partition; production deployments should automate
-- monthly partition creation (see backend-python/app/workers).
CREATE TABLE IF NOT EXISTS events_default PARTITION OF events DEFAULT;
CREATE INDEX IF NOT EXISTS idx_events_host ON events(host_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_entity ON events(entity_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type, occurred_at DESC);
