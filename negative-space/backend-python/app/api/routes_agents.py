"""Agent Management Center API - fleet health, silence separated from
service silence (Collector Integrity Monitor)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.db.database import get_db
from app.db.models import Agent

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.get("")
async def list_agents(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    rows = (
        await db.execute(select(Agent).where(Agent.tenant_id == user.tenant_id))
    ).scalars().all()
    now = datetime.now(timezone.utc)
    out = []
    for a in rows:
        gap = (now - a.last_seen_at).total_seconds() if a.last_seen_at else None
        derived_status = "offline" if (gap is None or gap > 120) else ("degraded" if gap > 60 else "online")
        out.append(
            {
                "id": str(a.id),
                "host_id": a.host_id,
                "agent_version": a.agent_version,
                "last_seen_at": a.last_seen_at,
                "seconds_since_last_seen": gap,
                "cpu_percent": a.cpu_percent,
                "memory_mb": a.memory_mb,
                "queue_depth": a.queue_depth,
                "dropped_events_total": a.dropped_events_total,
                "status": derived_status,
            }
        )
    return out
