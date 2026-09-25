"""Baseline / Expected Reality learning.

Learns the expected inter-arrival interval of a signal (heartbeat, log
line, audit event, ...) from historical observations using a robust
online estimator (EWMA of interval + EWMA of squared deviation for a
running standard deviation), rather than a single static threshold.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


EWMA_ALPHA = 0.2  # smoothing factor: higher = more reactive to recent intervals


@dataclass
class BaselineEstimate:
    expected_interval_seconds: float
    stddev_seconds: float
    confidence: float
    sample_count: int


class OnlineIntervalBaseline:
    """Incremental baseline estimator. Call `update()` on every observed
    inter-arrival interval; call `estimate()` to get the current
    expected interval + tolerance band."""

    def __init__(self, alpha: float = EWMA_ALPHA):
        self.alpha = alpha
        self.mean: float | None = None
        self.var: float = 0.0
        self.n: int = 0

    def update(self, interval_seconds: float) -> None:
        if interval_seconds <= 0:
            return
        self.n += 1
        if self.mean is None:
            self.mean = interval_seconds
            self.var = 0.0
            return
        delta = interval_seconds - self.mean
        self.mean += self.alpha * delta
        # EWMA of squared deviation approximates a running variance.
        self.var = (1 - self.alpha) * (self.var + self.alpha * delta * delta)

    def estimate(self) -> BaselineEstimate:
        if self.mean is None or self.n < 3:
            return BaselineEstimate(
                expected_interval_seconds=self.mean or 0.0,
                stddev_seconds=0.0,
                confidence=min(0.2, 0.05 * self.n),
                sample_count=self.n,
            )
        stddev = math.sqrt(max(self.var, 0.0))
        # Confidence grows with sample count and shrinks with relative
        # variance (a very noisy signal is a weaker baseline).
        cv = stddev / self.mean if self.mean > 0 else 1.0
        sample_confidence = min(1.0, self.n / 50.0)
        stability_confidence = max(0.1, 1.0 - min(cv, 1.0))
        confidence = round(0.5 * sample_confidence + 0.5 * stability_confidence, 3)
        return BaselineEstimate(
            expected_interval_seconds=round(self.mean, 3),
            stddev_seconds=round(stddev, 3),
            confidence=confidence,
            sample_count=self.n,
        )


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] + (s[c] - s[f]) * (k - f)


def ewma_series(values: list[float], alpha: float = EWMA_ALPHA) -> list[float]:
    """Simple EWMA smoothing, used by the Behavioral Drift Engine to
    detect gradual frequency decay that a single-point threshold would miss."""
    out: list[float] = []
    avg = None
    for v in values:
        avg = v if avg is None else alpha * v + (1 - alpha) * avg
        out.append(avg)
    return out


def cusum(values: list[float], target: float, drift: float = 0.5, threshold: float = 5.0) -> list[int]:
    """Change-point detector (CUSUM). Returns indices where a sustained
    upward or downward shift from `target` is flagged - used to catch
    a slow drift in event frequency that precedes a full silence."""
    pos, neg = 0.0, 0.0
    flags: list[int] = []
    for i, v in enumerate(values):
        pos = max(0.0, pos + (v - target) - drift)
        neg = min(0.0, neg + (v - target) + drift)
        if pos > threshold or abs(neg) > threshold:
            flags.append(i)
            pos, neg = 0.0, 0.0
    return flags
