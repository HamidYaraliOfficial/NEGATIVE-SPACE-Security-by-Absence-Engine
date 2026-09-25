"""Negative Space Detection Engine - the orchestrator.

Periodically (see app/workers/background_tasks.py) walks every active
ExpectedSignal, runs it through the Data Availability layer + Temporal
Silence Analyzer, and - only when a silence is judged meaningful and not
inside a declared maintenance window - writes a Detection row with a
full, explainable evidence bundle.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_hours import is_within_maintenance
from app.core.confidence import ConfidenceInputs, compute_confidence
from app.core.data_quality import CollectorHealth, classify_silence, data_quality_score
from app.core.silence_analyzer import analyze_silence
from app.db.models import Agent, BusinessHours, Detection, Entity, ExpectedSignal, Observation


async def run_detection_sweep(db: AsyncSession, tenant_id: str = "default") -> list[Detection]:
    """One full pass over all active expectations. Returns newly created
    detections (also persisted). Safe to call on a fixed interval."""
    created: list[Detection] = []
    now = datetime.now(timezone.utc)

    expected_rows = (
        await db.execute(select(ExpectedSignal).where(ExpectedSignal.status == "active"))
    ).scalars().all()

    for expected in expected_rows:
        obs = (
            await db.execute(
                select(Observation).where(
                    Observation.entity_id == expected.entity_id,
                    Observation.signal_name == expected.signal_name,
                )
            )
        ).scalar_one_or_none()
        if obs is None:
            continue  # never observed at all yet - not enough history to call this a silence

        verdict = analyze_silence(
            last_seen_at=obs.last_seen_at,
            expected_interval_seconds=expected.expected_interval_seconds,
            stddev_seconds=expected.interval_stddev_seconds,
            tolerance_multiplier=expected.tolerance_multiplier,
            now=now,
        )
        if not verdict.is_silent:
            continue

        entity = await db.get(Entity, expected.entity_id)
        if entity is None:
            continue

        # --- Maintenance window check ---
        maint_rows = (
            await db.execute(
                select(BusinessHours).where(
                    BusinessHours.is_maintenance_window == True,  # noqa: E712
                    BusinessHours.active == True,  # noqa: E712
                    (BusinessHours.entity_id == entity.id) | (BusinessHours.entity_id.is_(None)),
                )
            )
        ).scalars().all()
        if is_within_maintenance([{"schedule": m.schedule} for m in maint_rows], now):
            continue

        # --- Data Availability Confidence Layer ---
        agent = (
            await db.execute(select(Agent).where(Agent.tenant_id == tenant_id))
        ).scalars().first()
        health = CollectorHealth(
            agent_last_seen_at=agent.last_seen_at if agent else None,
            agent_status=agent.status if agent else "unknown",
            dropped_events_total=agent.dropped_events_total if agent else 0,
        )
        silence_class = classify_silence(health, now)
        if silence_class == "collector_failure":
            # This is a collector problem, not a security-meaningful
            # silence - surfaced separately via the Collector Integrity
            # Monitor / Agent Health endpoints instead of as a Detection.
            continue
        dq_score = data_quality_score(health, now)

        confidence = compute_confidence(
            ConfidenceInputs(
                baseline_confidence=expected.confidence,
                data_quality_score=dq_score,
                evidence_count=max(1, verdict.missed_cycles),
                context_match_score=0.8 if silence_class == "meaningful_silence" else 0.5,
            )
        )

        detection = Detection(
            tenant_id=tenant_id,
            entity_id=entity.id,
            category=f"missing_{expected.signal_name}",
            level="temporal",
            severity=confidence.severity,
            confidence=confidence.score,
            silence_started_at=verdict.silence_started_at or obs.last_seen_at,
            detected_at=now,
            expected_summary=(
                f"{entity.name} was expected to emit '{expected.signal_name}' "
                f"every ~{round(expected.expected_interval_seconds)}s "
                f"(±{round(verdict.tolerance_seconds)}s tolerance)."
            ),
            observed_summary=(
                f"No '{expected.signal_name}' observed for {round(verdict.gap_seconds)}s "
                f"({verdict.missed_cycles} missed cycle(s)). Last seen at {obs.last_seen_at.isoformat()}."
            ),
            evidence={
                "baseline_version": expected.version,
                "baseline_source": expected.source,
                "data_quality_score": dq_score,
                "silence_classification": silence_class,
                "confidence_components": confidence.components,
                "gap_seconds": verdict.gap_seconds,
                "missed_cycles": verdict.missed_cycles,
            },
            baseline_version=expected.version,
        )
        db.add(detection)
        created.append(detection)

    if created:
        await db.flush()
    return created
