"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    tenant_id: str


class EntityCreate(BaseModel):
    entity_type: str
    name: str
    criticality: str = "medium"
    attributes: dict[str, Any] = Field(default_factory=dict)


class EntityOut(BaseModel):
    id: str
    entity_type: str
    name: str
    criticality: str
    attributes: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class IngestEventEnvelope(BaseModel):
    event_id: str
    host_id: str
    tenant_id: str
    agent_version: str
    occurred_at: datetime
    captured_at: datetime
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)


class IngestBatch(BaseModel):
    host_id: str
    tenant_id: str
    events: list[dict[str, Any]]


class DetectionOut(BaseModel):
    id: str
    entity_id: str
    category: str
    level: str
    severity: str
    confidence: float
    silence_started_at: datetime
    detected_at: datetime
    expected_summary: str
    observed_summary: str
    evidence: dict[str, Any]
    status: str
    review_verdict: str

    class Config:
        from_attributes = True


class DetectionReview(BaseModel):
    verdict: str  # expected | maintenance | collector_issue | baseline_error | true_incident_candidate
    note: str = ""


class CaseCreate(BaseModel):
    title: str
    priority: str = "medium"
    owner: str = ""
    tags: list[str] = Field(default_factory=list)
    detection_ids: list[str] = Field(default_factory=list)


class CaseOut(BaseModel):
    id: str
    title: str
    status: str
    priority: str
    owner: str
    notes: list[Any]
    tags: list[Any]
    created_at: datetime

    class Config:
        from_attributes = True


class CaseNote(BaseModel):
    author: str
    text: str


class BusinessHoursCreate(BaseModel):
    entity_id: str | None = None
    name: str
    timezone: str = "UTC"
    schedule: dict[str, list[list[str]]]
    is_maintenance_window: bool = False


class BusinessHoursOut(BaseModel):
    id: str
    entity_id: str | None
    name: str
    timezone: str
    schedule: dict[str, Any]
    is_maintenance_window: bool
    active: bool

    class Config:
        from_attributes = True


class BusinessHoursStatusOut(BaseModel):
    is_open: bool
    current_window: list[str] | None
    next_open_at: datetime | None
    seconds_until_next_open: float | None
    next_window_duration_seconds: float | None


class RelationshipUpsert(BaseModel):
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    expected: bool = True
    observed: bool = True
    frequency_per_day: float = 0.0
    confidence: float = 0.5


class QueryRequest(BaseModel):
    time_range_hours: float = 24
    entity_type: str | None = None
    entity_name_contains: str | None = None
    category: str | None = None
    min_confidence: float = 0.0
    relationship_state: str | None = None
    limit: int = 200
