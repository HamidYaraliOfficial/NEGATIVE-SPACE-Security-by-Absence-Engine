"""Expected Reality Model - the service layer that learns and stores
per-entity expectations (ExpectedSignal rows) from a stream of
observation intervals, and exposes them to the Detection Engine.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.baseline import OnlineIntervalBaseline
from app.db.models import ExpectedSignal, Observation


async def record_observation(
    db: AsyncSession, entity_id: str, signal_name: str, occurred_at: datetime
) -> None:
    """Update the last-seen ledger and feed the interval into the
    entity's baseline estimator, persisting the refreshed expectation."""
    result = await db.execute(
        select(Observation).where(
            Observation.entity_id == entity_id, Observation.signal_name == signal_name
        )
    )
    obs = result.scalar_one_or_none()

    result = await db.execute(
        select(ExpectedSignal).where(
            ExpectedSignal.entity_id == entity_id, ExpectedSignal.signal_name == signal_name
        )
    )
    expected = result.scalar_one_or_none()

    estimator = OnlineIntervalBaseline()
    if expected is not None:
        # Reconstruct estimator state from stored summary stats so we can
        # keep updating incrementally without replaying full history.
        estimator.mean = expected.expected_interval_seconds
        estimator.var = expected.interval_stddev_seconds ** 2
        estimator.n = max(expected.confidence * 50, 1)

    if obs is not None:
        interval = (occurred_at - obs.last_seen_at).total_seconds()
        if interval > 0:
            estimator.update(interval)
        obs.last_seen_at = occurred_at
        obs.observed_count += 1
        obs.last_interval_seconds = interval
    else:
        obs = Observation(
            entity_id=entity_id,
            signal_name=signal_name,
            last_seen_at=occurred_at,
            observed_count=1,
            last_interval_seconds=0.0,
        )
        db.add(obs)

    est = estimator.estimate()
    if expected is None:
        expected = ExpectedSignal(
            entity_id=entity_id,
            signal_name=signal_name,
            expected_interval_seconds=est.expected_interval_seconds or 60.0,
            interval_stddev_seconds=est.stddev_seconds,
            confidence=est.confidence,
            source="learned",
            explanation="Learned online from observed inter-arrival intervals.",
            updated_at=datetime.now(timezone.utc),
        )
        db.add(expected)
    elif expected.status == "active":
        expected.expected_interval_seconds = est.expected_interval_seconds or expected.expected_interval_seconds
        expected.interval_stddev_seconds = est.stddev_seconds
        expected.confidence = est.confidence
        expected.updated_at = datetime.now(timezone.utc)
    # status == "frozen" -> poisoning protection: do not update while frozen.

    await db.flush()
