"""Temporal Silence Analyzer.

Given a signal's baseline (expected interval + stddev) and its last
observed timestamp, decides whether the current gap constitutes a
meaningful, evidence-backed silence - and if so, since when.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class SilenceVerdict:
    is_silent: bool
    gap_seconds: float
    expected_interval_seconds: float
    tolerance_seconds: float
    missed_cycles: int
    silence_started_at: datetime | None


def analyze_silence(
    last_seen_at: datetime,
    expected_interval_seconds: float,
    stddev_seconds: float,
    tolerance_multiplier: float,
    now: datetime | None = None,
) -> SilenceVerdict:
    now = now or datetime.now(timezone.utc)
    gap = (now - last_seen_at).total_seconds()

    # Tolerance band: expected interval plus a multiple of the observed
    # standard deviation, with a sane floor so near-zero-variance signals
    # (e.g. an exact 30s heartbeat) don't trigger on tiny jitter.
    tolerance = max(
        expected_interval_seconds * 0.25,
        tolerance_multiplier * max(stddev_seconds, expected_interval_seconds * 0.05),
    )

    threshold = expected_interval_seconds + tolerance
    is_silent = expected_interval_seconds > 0 and gap > threshold

    missed_cycles = 0
    silence_started_at = None
    if is_silent and expected_interval_seconds > 0:
        missed_cycles = int(gap // expected_interval_seconds)
        silence_started_at = last_seen_at

    return SilenceVerdict(
        is_silent=is_silent,
        gap_seconds=round(gap, 3),
        expected_interval_seconds=expected_interval_seconds,
        tolerance_seconds=round(tolerance, 3),
        missed_cycles=missed_cycles,
        silence_started_at=silence_started_at,
    )
