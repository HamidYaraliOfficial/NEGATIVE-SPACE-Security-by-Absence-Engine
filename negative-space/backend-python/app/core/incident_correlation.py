"""Incident Correlation Engine + First Divergence Detector.

Groups temporally- and relationally-close detections into a single
Compound Silence Incident, and identifies the first point in the
timeline where observed behavior split from expected behavior.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class DetectionRef:
    id: str
    entity_id: str
    detected_at: datetime
    silence_started_at: datetime
    category: str
    related_entity_ids: set[str]


def correlate(
    detections: list[DetectionRef],
    time_window: timedelta = timedelta(minutes=15),
) -> list[list[DetectionRef]]:
    """Union-find style clustering: two detections are linked if they are
    within `time_window` of each other AND share/relate an entity."""
    n = len(detections)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(n):
        for j in range(i + 1, n):
            a, b = detections[i], detections[j]
            close_in_time = abs((a.detected_at - b.detected_at).total_seconds()) <= time_window.total_seconds()
            shares_entity = (
                a.entity_id == b.entity_id
                or a.entity_id in b.related_entity_ids
                or b.entity_id in a.related_entity_ids
            )
            if close_in_time and shares_entity:
                union(i, j)

    clusters: dict[int, list[DetectionRef]] = {}
    for i, d in enumerate(detections):
        clusters.setdefault(find(i), []).append(d)

    return [c for c in clusters.values() if len(c) >= 1]


def first_divergence(cluster: list[DetectionRef]) -> DetectionRef | None:
    """The earliest silence_started_at across the cluster is treated as
    the first point observed reality split from expected reality."""
    if not cluster:
        return None
    return min(cluster, key=lambda d: d.silence_started_at)


def compound_incident_title(cluster: list[DetectionRef]) -> str:
    categories = sorted({d.category for d in cluster})
    entities = sorted({d.entity_id for d in cluster})
    return f"Compound silence across {len(entities)} entities ({', '.join(categories[:3])})"
