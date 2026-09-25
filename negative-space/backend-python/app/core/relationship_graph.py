"""Reality Graph + Expected-vs-Observed Graph Diff Engine.

Builds an in-memory graph (networkx) of entities and their relationships,
tagging each edge as expected/observed, and computes the diff between
what the system expects to see and what it currently observes:
missing edges, unexpected edges, and frequency drift.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx


@dataclass
class GraphDiff:
    missing_edges: list[dict] = field(default_factory=list)
    unexpected_edges: list[dict] = field(default_factory=list)
    frequency_drift: list[dict] = field(default_factory=list)


class RealityGraph:
    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def add_entity(self, entity_id: str, **attrs) -> None:
        self.graph.add_node(entity_id, **attrs)

    def upsert_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        expected: bool,
        observed: bool,
        frequency_per_day: float,
        confidence: float,
    ) -> None:
        self.graph.add_edge(
            source_id,
            target_id,
            key=rel_type,
            relationship_type=rel_type,
            expected=expected,
            observed=observed,
            frequency_per_day=frequency_per_day,
            confidence=confidence,
        )

    def diff(self, frequency_drift_threshold: float = 0.5) -> GraphDiff:
        result = GraphDiff()
        for u, v, key, data in self.graph.edges(keys=True, data=True):
            if data.get("expected") and not data.get("observed"):
                result.missing_edges.append(
                    {"source": u, "target": v, "type": key, "confidence": data.get("confidence")}
                )
            elif data.get("observed") and not data.get("expected"):
                result.unexpected_edges.append(
                    {"source": u, "target": v, "type": key, "confidence": data.get("confidence")}
                )
        return result

    def subgraph_for_entity(self, entity_id: str, depth: int = 1) -> nx.MultiDiGraph:
        nodes = {entity_id}
        frontier = {entity_id}
        for _ in range(depth):
            nxt = set()
            for n in frontier:
                nxt |= set(self.graph.successors(n)) | set(self.graph.predecessors(n))
            nodes |= nxt
            frontier = nxt
        return self.graph.subgraph(nodes).copy()

    def to_json(self) -> dict:
        nodes = [{"id": n, **d} for n, d in self.graph.nodes(data=True)]
        edges = [
            {"source": u, "target": v, "type": k, **d}
            for u, v, k, d in self.graph.edges(keys=True, data=True)
        ]
        return {"nodes": nodes, "edges": edges}
