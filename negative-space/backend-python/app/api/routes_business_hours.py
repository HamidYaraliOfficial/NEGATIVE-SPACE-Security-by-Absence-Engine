"""Business Hours / Maintenance Window API.

Lets the user enter, per entity (or globally), a weekly schedule of open
hours. The status endpoint always computes, live: is it open right now,
and if not - the exact time of the next opening and how long that next
window will last.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.business_hours import evaluate_schedule
from app.db.database import get_db
from app.db.models import BusinessHours
from app.schemas.schemas import BusinessHoursCreate, BusinessHoursOut, BusinessHoursStatusOut

router = APIRouter(prefix="/api/v1/business-hours", tags=["business-hours"])


@router.get("", response_model=list[BusinessHoursOut])
async def list_business_hours(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    rows = (
        await db.execute(select(BusinessHours).where(BusinessHours.tenant_id == user.tenant_id))
    ).scalars().all()
    return [_serialize(r) for r in rows]


@router.post("", response_model=BusinessHoursOut)
async def create_business_hours(
    body: BusinessHoursCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    row = BusinessHours(
        tenant_id=user.tenant_id,
        entity_id=body.entity_id,
        name=body.name,
        timezone=body.timezone,
        schedule=body.schedule,
        is_maintenance_window=body.is_maintenance_window,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _serialize(row)


@router.get("/{business_hours_id}/status", response_model=BusinessHoursStatusOut)
async def get_status(
    business_hours_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    row = await db.get(BusinessHours, business_hours_id)
    now = datetime.now(timezone.utc)
    result = evaluate_schedule(row.schedule, now)
    return BusinessHoursStatusOut(
        is_open=result.is_open,
        current_window=list(result.current_window) if result.current_window else None,
        next_open_at=result.next_open_at,
        seconds_until_next_open=result.seconds_until_next_open,
        next_window_duration_seconds=result.next_window_duration_seconds,
    )


@router.delete("/{business_hours_id}")
async def delete_business_hours(
    business_hours_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    row = await db.get(BusinessHours, business_hours_id)
    if row:
        await db.delete(row)
        await db.commit()
    return {"deleted": True}


def _serialize(r: BusinessHours) -> dict:
    return {
        "id": str(r.id),
        "entity_id": str(r.entity_id) if r.entity_id else None,
        "name": r.name,
        "timezone": r.timezone,
        "schedule": r.schedule,
        "is_maintenance_window": r.is_maintenance_window,
        "active": r.active,
    }
