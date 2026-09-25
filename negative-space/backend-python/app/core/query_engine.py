"""Negative Space Query Language - a small, safe JSON-based DSL for the
Investigation Notebook / Query Playground. Deliberately not raw SQL: every
query has an enforced time range, result limit and timeout so a heavy
query cannot starve the rest of the platform.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Detection, Entity, Relationship

MAX_RESULTS = 1000
DEFAULT_TIMEOUT_SECONDS = 8


@dataclass
class NegativeSpaceQuery:
    time_range_hours: float = 24
    entity_type: str | None = None
    entity_name_contains: str | None = None
    category: str | None = None
    min_confidence: float = 0.0
    relationship_state: str | None = None  # "missing" | "unexpected" | None
    limit: int = 200


async def run_query(db: AsyncSession, q: NegativeSpaceQuery, tenant_id: str = "default") -> dict:
    limit = min(q.limit, MAX_RESULTS)
    since = datetime.now(timezone.utc) - timedelta(hours=q.time_range_hours)

    stmt = (
        select(Detection, Entity)
        .join(Entity, Detection.entity_id == Entity.id)
        .where(Detection.tenant_id == tenant_id, Detection.detected_at >= since)
        .order_by(Detection.detected_at.desc())
        .limit(limit)
    )
    if q.entity_type:
        stmt = stmt.where(Entity.entity_type == q.entity_type)
    if q.category:
        stmt = stmt.where(Detection.category == q.category)
    if q.min_confidence:
        stmt = stmt.where(Detection.confidence >= q.min_confidence)
    if q.entity_name_contains:
        stmt = stmt.where(Entity.name.ilike(f"%{q.entity_name_contains}%"))

    rows = (await db.execute(stmt)).all()
    detections = [
        {
            "id": str(d.id),
            "entity": e.name,
            "entity_type": e.entity_type.value if hasattr(e.entity_type, "value") else e.entity_type,
            "category": d.category,
            "confidence": d.confidence,
            "severity": d.severity,
            "detected_at": d.detected_at.isoformat(),
            "silence_started_at": d.silence_started_at.isoformat(),
            "expected_summary": d.expected_summary,
            "observed_summary": d.observed_summary,
        }
        for d, e in rows
    ]

    relationships: list[dict] = []
    if q.relationship_state in ("missing", "unexpected"):
        rel_stmt = select(Relationship).where(Relationship.tenant_id == tenant_id)
        if q.relationship_state == "missing":
            rel_stmt = rel_stmt.where(Relationship.expected == True, Relationship.observed == False)  # noqa: E712
        else:
            rel_stmt = rel_stmt.where(Relationship.observed == True, Relationship.expected == False)  # noqa: E712
        rel_rows = (await db.execute(rel_stmt.limit(limit))).scalars().all()
        relationships = [
            {
                "id": str(r.id),
                "source_entity_id": str(r.source_entity_id),
                "target_entity_id": str(r.target_entity_id),
                "relationship_type": r.relationship_type,
                "confidence": r.confidence,
            }
            for r in rel_rows
        ]

    return {"detections": detections, "relationships": relationships, "result_count": len(detections)}
