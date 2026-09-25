"""Core ORM models. Mirrors app/db/schema.sql (used for local dev /
Alembic autogeneration reference)."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def uuid_col():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Role(str, enum.Enum):
    admin = "admin"
    engineer = "engineer"
    analyst = "analyst"
    auditor = "auditor"


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = uuid_col()
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.analyst)
    tenant_id: Mapped[str] = mapped_column(String(64), default="default")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class EntityType(str, enum.Enum):
    host = "host"
    service = "service"
    process = "process"
    container = "container"
    user = "user"
    api = "api"
    database = "database"
    network_connection = "network_connection"
    scheduled_job = "scheduled_job"
    auth_flow = "auth_flow"
    log_source = "log_source"
    audit_stream = "audit_stream"
    health_check = "health_check"
    telemetry_channel = "telemetry_channel"
    security_control = "security_control"


class Entity(Base):
    __tablename__ = "entities"
    id: Mapped[uuid.UUID] = uuid_col()
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, default="default")
    entity_type: Mapped[EntityType] = mapped_column(Enum(EntityType), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    criticality: Mapped[str] = mapped_column(String(32), default="medium")  # low/medium/high/critical
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("tenant_id", "entity_type", "name", name="uq_entity_identity"),)


class ExpectedSignal(Base):
    """One row = one learned/declared expectation for an entity+signal."""
    __tablename__ = "expected_signals"
    id: Mapped[uuid.UUID] = uuid_col()
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id"), index=True)
    signal_name: Mapped[str] = mapped_column(String(128))  # e.g. "heartbeat", "audit_event"
    expected_interval_seconds: Mapped[float] = mapped_column(Float)
    interval_stddev_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    tolerance_multiplier: Mapped[float] = mapped_column(Float, default=2.5)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    context: Mapped[dict] = mapped_column(JSON, default=dict)  # host/env/time-of-day scoping
    source: Mapped[str] = mapped_column(String(64), default="learned")  # learned | declared
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="active")  # active|frozen|deprecated
    explanation: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    entity: Mapped["Entity"] = relationship()


class Observation(Base):
    """Latest-known-state / last-seen ledger per entity+signal, updated on
    every ingested event. This is what the Silence Analyzer diffs against
    ExpectedSignal."""
    __tablename__ = "observations"
    id: Mapped[uuid.UUID] = uuid_col()
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id"), index=True)
    signal_name: Mapped[str] = mapped_column(String(128), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    observed_count: Mapped[int] = mapped_column(Integer, default=0)
    last_interval_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    __table_args__ = (UniqueConstraint("entity_id", "signal_name", name="uq_observation"),)


class Detection(Base):
    __tablename__ = "detections"
    id: Mapped[uuid.UUID] = uuid_col()
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, default="default")
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id"), index=True)
    category: Mapped[str] = mapped_column(String(64))  # missing_heartbeat, missing_relationship, drift, ...
    level: Mapped[str] = mapped_column(String(32))     # temporal | relational | semantic
    severity: Mapped[str] = mapped_column(String(16), default="medium")
    confidence: Mapped[float] = mapped_column(Float)
    silence_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    expected_summary: Mapped[str] = mapped_column(Text)
    observed_summary: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    baseline_version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="open")  # open|reviewed|closed
    review_verdict: Mapped[str] = mapped_column(String(32), default="")  # expected|maintenance|collector_issue|baseline_error|true_incident
    case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cases.id"), nullable=True)

    entity: Mapped["Entity"] = relationship()


class Relationship(Base):
    __tablename__ = "relationships"
    id: Mapped[uuid.UUID] = uuid_col()
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, default="default")
    source_entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id"), index=True)
    target_entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id"), index=True)
    relationship_type: Mapped[str] = mapped_column(String(64))  # connects_to, depends_on, authenticates_via...
    expected: Mapped[bool] = mapped_column(Boolean, default=True)
    observed: Mapped[bool] = mapped_column(Boolean, default=True)
    frequency_per_day: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    last_observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_learned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[uuid.UUID] = uuid_col()
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, default="default")
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="open")
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    first_divergence_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recovered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    detection_ids: Mapped[list] = mapped_column(JSON, default=list)
    timeline: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Case(Base):
    __tablename__ = "cases"
    id: Mapped[uuid.UUID] = uuid_col()
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, default="default")
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="open")  # open|investigating|contained|resolved|closed
    priority: Mapped[str] = mapped_column(String(16), default="medium")
    owner: Mapped[str] = mapped_column(String(255), default="")
    notes: Mapped[list] = mapped_column(JSON, default=list)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Agent(Base):
    __tablename__ = "agents"
    id: Mapped[uuid.UUID] = uuid_col()
    host_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), default="default")
    agent_version: Mapped[str] = mapped_column(String(32), default="")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cpu_percent: Mapped[float] = mapped_column(Float, default=0.0)
    memory_mb: Mapped[float] = mapped_column(Float, default=0.0)
    queue_depth: Mapped[int] = mapped_column(Integer, default=0)
    dropped_events_total: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="unknown")  # online|degraded|offline
    config: Mapped[dict] = mapped_column(JSON, default=dict)


class BusinessHours(Base):
    """User-configurable open/closed schedule per entity, used by the
    Maintenance Window / Business Context engines to avoid raising
    detections during expected downtime."""
    __tablename__ = "business_hours"
    id: Mapped[uuid.UUID] = uuid_col()
    entity_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("entities.id"), nullable=True)
    tenant_id: Mapped[str] = mapped_column(String(64), default="default")
    name: Mapped[str] = mapped_column(String(255))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    # weekly schedule: {"mon": [["09:00","18:00"]], "tue": [...], ...}
    schedule: Mapped[dict] = mapped_column(JSON, default=dict)
    is_maintenance_window: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[uuid.UUID] = uuid_col()
    tenant_id: Mapped[str] = mapped_column(String(64), default="default")
    actor: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(128))
    target: Mapped[str] = mapped_column(String(255), default="")
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
