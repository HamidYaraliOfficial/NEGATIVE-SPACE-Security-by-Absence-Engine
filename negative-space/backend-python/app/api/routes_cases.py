"""Case Management System."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.db.database import get_db
from app.db.models import Case
from app.schemas.schemas import CaseCreate, CaseNote, CaseOut

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])


@router.get("", response_model=list[CaseOut])
async def list_cases(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    rows = (
        await db.execute(
            select(Case).where(Case.tenant_id == user.tenant_id).order_by(Case.created_at.desc())
        )
    ).scalars().all()
    return [_serialize(c) for c in rows]


@router.post("", response_model=CaseOut)
async def create_case(
    body: CaseCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    case = Case(
        tenant_id=user.tenant_id,
        title=body.title,
        priority=body.priority,
        owner=body.owner,
        tags=body.tags,
    )
    db.add(case)
    await db.flush()

    if body.detection_ids:
        from app.db.models import Detection
        for det_id in body.detection_ids:
            det = await db.get(Detection, det_id)
            if det:
                det.case_id = case.id

    await db.commit()
    await db.refresh(case)
    return _serialize(case)


@router.post("/{case_id}/notes", response_model=CaseOut)
async def add_note(
    case_id: str,
    body: CaseNote,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    case = await db.get(Case, case_id)
    case.notes = [*case.notes, {"author": body.author, "text": body.text, "at": datetime.now(timezone.utc).isoformat()}]
    await db.commit()
    await db.refresh(case)
    return _serialize(case)


@router.post("/{case_id}/status/{new_status}", response_model=CaseOut)
async def set_status(
    case_id: str,
    new_status: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    case = await db.get(Case, case_id)
    case.status = new_status
    if new_status in ("resolved", "closed"):
        case.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(case)
    return _serialize(case)


def _serialize(c: Case) -> dict:
    return {
        "id": str(c.id),
        "title": c.title,
        "status": c.status,
        "priority": c.priority,
        "owner": c.owner,
        "notes": c.notes,
        "tags": c.tags,
        "created_at": c.created_at,
    }
