"""Ingestion endpoint the Rust agent ships batches to. Normalizes each
canonical event into the Observation ledger (feeding the Expected
Reality Model) and the raw `events` evidence table, and updates the
Agent's own self-health row (Collector Integrity Monitor)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.expected_reality import record_observation
from app.db.database import get_db
from app.db.models import Agent, Entity, EntityType
from app.schemas.schemas import IngestBatch

router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])


async def _get_or_create_host_entity(db: AsyncSession, tenant_id: str, host_id: str) -> Entity:
    result = await db.execute(
        select(Entity).where(
            Entity.tenant_id == tenant_id, Entity.entity_type == EntityType.host, Entity.name == host_id
        )
    )
    entity = result.scalar_one_or_none()
    if entity is None:
        entity = Entity(tenant_id=tenant_id, entity_type=EntityType.host, name=host_id)
        db.add(entity)
        await db.flush()
    return entity


@router.post("/events")
async def ingest_events(
    batch: IngestBatch,
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing agent token")

    now = datetime.now(timezone.utc)
    host_entity = await _get_or_create_host_entity(db, batch.tenant_id, batch.host_id)

    agent = (await db.execute(select(Agent).where(Agent.host_id == batch.host_id))).scalar_one_or_none()
    if agent is None:
        agent = Agent(host_id=batch.host_id, tenant_id=batch.tenant_id, status="online")
        db.add(agent)
    agent.last_seen_at = now
    agent.status = "online"

    for raw in batch.events:
        event_type = raw.get("event_type")
        occurred_at_raw = raw.get("occurred_at")
        try:
            occurred_at = datetime.fromisoformat(occurred_at_raw.replace("Z", "+00:00")) if occurred_at_raw else now
        except Exception:
            occurred_at = now

        if event_type == "heartbeat":
            await record_observation(db, str(host_entity.id), "heartbeat", occurred_at)
        elif event_type == "agent_health":
            agent.cpu_percent = raw.get("cpu_percent", agent.cpu_percent)
            agent.memory_mb = raw.get("memory_mb", agent.memory_mb)
            agent.queue_depth = raw.get("queue_depth", agent.queue_depth)
            agent.dropped_events_total = raw.get("dropped_events_total", agent.dropped_events_total)
        elif event_type == "process_lifecycle":
            await record_observation(db, str(host_entity.id), "process_activity", occurred_at)
        elif event_type == "network_connection":
            await record_observation(db, str(host_entity.id), "network_activity", occurred_at)

    await db.commit()
    return {"accepted": len(batch.events)}
