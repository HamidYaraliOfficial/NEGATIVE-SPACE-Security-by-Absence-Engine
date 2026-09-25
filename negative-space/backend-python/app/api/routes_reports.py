"""Security Posture Dashboard summary + basic export."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.db.database import get_db
from app.db.models import Agent, Detection, Entity, Incident, Relationship

router = APIRouter(prefix="/api/v1/posture", tags=["posture"])


@router.get("/summary")
async def posture_summary(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    since_24h = datetime.now(timezone.utc) - timedelta(hours=24)

    entity_count = (
        await db.execute(select(func.count()).select_from(Entity).where(Entity.tenant_id == user.tenant_id))
    ).scalar_one()
    open_detections = (
        await db.execute(
            select(func.count()).select_from(Detection).where(
                Detection.tenant_id == user.tenant_id, Detection.status == "open"
            )
        )
    ).scalar_one()
    detections_24h = (
        await db.execute(
            select(func.count()).select_from(Detection).where(
                Detection.tenant_id == user.tenant_id, Detection.detected_at >= since_24h
            )
        )
    ).scalar_one()
    critical_open = (
        await db.execute(
            select(func.count()).select_from(Detection).where(
                Detection.tenant_id == user.tenant_id,
                Detection.status == "open",
                Detection.severity == "critical",
            )
        )
    ).scalar_one()
    active_incidents = (
        await db.execute(
            select(func.count()).select_from(Incident).where(
                Incident.tenant_id == user.tenant_id, Incident.status == "open"
            )
        )
    ).scalar_one()
    missing_relationships = (
        await db.execute(
            select(func.count()).select_from(Relationship).where(
                Relationship.tenant_id == user.tenant_id,
                Relationship.expected == True,  # noqa: E712
                Relationship.observed == False,  # noqa: E712
            )
        )
    ).scalar_one()
    agents = (await db.execute(select(Agent).where(Agent.tenant_id == user.tenant_id))).scalars().all()
    now = datetime.now(timezone.utc)
    agents_online = sum(
        1 for a in agents if a.last_seen_at and (now - a.last_seen_at).total_seconds() < 120
    )

    return {
        "entity_count": entity_count,
        "open_detections": open_detections,
        "critical_open_detections": critical_open,
        "detections_last_24h": detections_24h,
        "active_incidents": active_incidents,
        "missing_relationships": missing_relationships,
        "agents_total": len(agents),
        "agents_online": agents_online,
        "blind_spot_ratio": round(1 - (agents_online / len(agents)), 3) if agents else 0.0,
    }
