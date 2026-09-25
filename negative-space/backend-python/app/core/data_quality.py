"""Data Availability Confidence Layer.

Before the Detection Engine is allowed to say "this silence is real", it
must consult this layer to rule out the mundane explanation: the
collector itself went dark. Separates "signal truly stopped" from
"we stopped being able to see the signal".
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class CollectorHealth:
    agent_last_seen_at: datetime | None
    agent_status: str            # online | degraded | offline | unknown
    dropped_events_total: int
    expected_agent_heartbeat_seconds: int = 30


def agent_is_silent(health: CollectorHealth, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    if health.agent_last_seen_at is None:
        return True
    gap = (now - health.agent_last_seen_at).total_seconds()
    return gap > (health.expected_agent_heartbeat_seconds * 4)


def data_quality_score(health: CollectorHealth, now: datetime | None = None) -> float:
    """0..1 - how much we should trust an observed silence as meaningful,
    given the health of the pipe carrying that signal to us."""
    now = now or datetime.now(timezone.utc)
    if agent_is_silent(health, now):
        # If the collector itself is dark, we cannot trust silence from
        # anything it was responsible for observing.
        return 0.05

    score = 1.0
    if health.agent_status == "degraded":
        score -= 0.35
    elif health.agent_status == "unknown":
        score -= 0.5

    if health.dropped_events_total > 0:
        # Some drops are normal under load; scale the penalty logarithmically.
        import math
        score -= min(0.3, 0.05 * math.log1p(health.dropped_events_total))

    return round(max(0.0, min(1.0, score)), 3)


def classify_silence(
    health: CollectorHealth, now: datetime | None = None
) -> str:
    """Returns 'meaningful_silence', 'collector_failure', or 'degraded_confidence'."""
    now = now or datetime.now(timezone.utc)
    if agent_is_silent(health, now):
        return "collector_failure"
    if health.agent_status == "degraded" or health.dropped_events_total > 100:
        return "degraded_confidence"
    return "meaningful_silence"
