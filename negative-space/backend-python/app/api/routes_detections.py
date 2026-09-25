"""Detections + on-demand sweep trigger + False Positive Review Engine."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.detection_engine import run_detection_sweep
from app.db.database import get_db
from app.db.models import Detection
from app.schemas.schemas import DetectionOut, DetectionReview

router = APIRouter(prefix="/api/v1/detections", tags=["detections"])


@router.get("", response_model=list[DetectionOut])
async def list_detections(
    status_filter: str | None = None,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    stmt = select(Detection).where(Detection.tenant_id == user.tenant_id)
    if status_filter:
        stmt = stmt.where(Detection.status == status_filter)
    rows = (
        await db.execute(stmt.order_by(Detection.detected_at.desc()).limit(min(limit, 1000)))
    ).scalars().all()
    return [_serialize(d) for d in rows]


@router.post("/sweep")
async def trigger_sweep(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    created = await run_detection_sweep(db, tenant_id=user.tenant_id)
    await db.commit()
    return {"created": len(created)}


@router.post("/{detection_id}/review", response_model=DetectionOut)
async def review_detection(
    detection_id: str,
    body: DetectionReview,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    detection = await db.get(Detection, detection_id)
    detection.review_verdict = body.verdict
    detection.status = "reviewed" if body.verdict != "true_incident_candidate" else "open"
    await db.commit()
    await db.refresh(detection)
    return _serialize(detection)


def _serialize(d: Detection) -> dict:
    return {
        "id": str(d.id),
        "entity_id": str(d.entity_id),
        "category": d.category,
        "level": d.level,
        "severity": d.severity,
        "confidence": d.confidence,
        "silence_started_at": d.silence_started_at,
        "detected_at": d.detected_at,
        "expected_summary": d.expected_summary,
        "observed_summary": d.observed_summary,
        "evidence": d.evidence,
        "status": d.status,
        "review_verdict": d.review_verdict,
    }
