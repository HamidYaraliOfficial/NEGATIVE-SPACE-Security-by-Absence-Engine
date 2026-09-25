"use client";

import { useEffect, useState } from "react";
import { TopBar } from "@/components/TopBar";
import { useI18n } from "@/i18n/I18nProvider";
import { api } from "@/lib/api";

interface GraphNode { id: string; name: string; entity_type: string }
interface GraphEdge { source: string; target: string; type: string; expected: boolean; observed: boolean }
interface GraphResponse {
  graph: { nodes: GraphNode[]; edges: GraphEdge[] };
  diff: { missing_edges: unknown[]; unexpected_edges: unknown[] };
}

export default function RelationshipGraphPage() {
  const { t } = useI18n();
  const [data, setData] = useState<GraphResponse | null>(null);

  useEffect(() => {
    api
      .relationshipGraph()
      .then((d) => setData(d as GraphResponse))
      .catch(() => setData(null));
  }, []);

  const nodeById = new Map((data?.graph.nodes ?? []).map((n) => [n.id, n]));
  const radius = 180;
  const cx = 260;
  const cy = 220;
  const nodes = data?.graph.nodes ?? [];
  const positions = new Map(
    nodes.map((n, i) => {
      const angle = (2 * Math.PI * i) / Math.max(nodes.length, 1);
      return [n.id, { x: cx + radius * Math.cos(angle), y: cy + radius * Math.sin(angle) }];
    })
  );

  return (
    <div className="px-4">
      <TopBar
        title={t("nav.relationship_graph")}
        subtitle={`Missing edges: ${data?.diff.missing_edges.length ?? 0} · Unexpected edges: ${
          data?.diff.unexpected_edges.length ?? 0
        }`}
      />
      <div className="acrylic rounded-win p-4">
        {!data || nodes.length === 0 ? (
          <p className="text-ink-muted text-sm py-12 text-center">{t("common.no_data")}</p>
        ) : (
          <svg viewBox="0 0 520 440" className="w-full h-[440px]">
            {data.graph.edges.map((e, i) => {
              const s = positions.get(e.source);
              const tPos = positions.get(e.target);
              if (!s || !tPos) return null;
              const dashed = e.expected && !e.observed;
              const stroke = dashed ? "var(--ns-danger)" : e.observed && !e.expected ? "var(--ns-warn)" : "var(--ns-ink-muted)";
              return (
                <line
                  key={i}
                  x1={s.x}
                  y1={s.y}
                  x2={tPos.x}
                  y2={tPos.y}
                  stroke={stroke}
                  strokeWidth={1.5}
                  strokeDasharray={dashed ? "4 4" : undefined}
                  opacity={0.7}
                />
              );
            })}
            {nodes.map((n) => {
              const p = positions.get(n.id)!;
              return (
                <g key={n.id}>
                  <circle cx={p.x} cy={p.y} r={8} fill="var(--ns-accent)" />
                  <text x={p.x + 12} y={p.y + 4} fontSize={11} fill="var(--ns-ink)">
                    {n.name}
                  </text>
                </g>
              );
            })}
          </svg>
        )}
      </div>
    </div>
  );
}
