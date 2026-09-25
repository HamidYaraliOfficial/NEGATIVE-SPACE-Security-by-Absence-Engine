"""Detection Confidence Engine.

Every detection is scored, never just flagged. Confidence combines four
independent inputs so a UI/analyst can see *why* a silence was judged
meaningful rather than trusting a single opaque number.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConfidenceInputs:
    baseline_confidence: float          # how reliable is the expected-interval model itself
    data_quality_score: float           # collector/agent health, sampling, clock skew
    evidence_count: int                 # number of corroborating missing-signal observations
    context_match_score: float          # how well current context matches the baseline's learned context


@dataclass
class ConfidenceResult:
    score: float
    severity: str
    components: dict = field(default_factory=dict)


def evidence_count_factor(n: int) -> float:
    # Diminishing returns: 1 missing beat is weak evidence, 5+ is strong.
    return min(1.0, 0.25 + 0.15 * n)


def compute_confidence(inputs: ConfidenceInputs) -> ConfidenceResult:
    ev_factor = evidence_count_factor(inputs.evidence_count)
    weighted = (
        0.35 * inputs.baseline_confidence
        + 0.30 * inputs.data_quality_score
        + 0.20 * ev_factor
        + 0.15 * inputs.context_match_score
    )
    score = round(max(0.0, min(1.0, weighted)), 3)

    if score >= 0.85:
        severity = "critical"
    elif score >= 0.65:
        severity = "high"
    elif score >= 0.45:
        severity = "medium"
    else:
        severity = "low"

    return ConfidenceResult(
        score=score,
        severity=severity,
        components={
            "baseline_confidence": inputs.baseline_confidence,
            "data_quality_score": inputs.data_quality_score,
            "evidence_factor": round(ev_factor, 3),
            "context_match_score": inputs.context_match_score,
        },
    )
