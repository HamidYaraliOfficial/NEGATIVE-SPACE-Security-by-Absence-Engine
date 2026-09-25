"use client";

import { useEffect, useState } from "react";
import { TopBar } from "@/components/TopBar";
import { useI18n } from "@/i18n/I18nProvider";
import { api } from "@/lib/api";
import { AgentStatus } from "@/lib/types";

const statusColor: Record<string, string> = {
  online: "bg-ok/15 text-ok",
  degraded: "bg-warn/15 text-warn",
  offline: "bg-danger/15 text-danger",
};

export default function AgentsPage() {
  const { t } = useI18n();
  const [agents, setAgents] = useState<AgentStatus[]>([]);

  useEffect(() => {
    api
      .listAgents()
      .then((a) => setAgents(a as AgentStatus[]))
      .catch(() => setAgents([]));
  }, []);

  return (
    <div className="px-4">
      <TopBar title={t("nav.agent_management")} subtitle="Fleet health — agent silence is tracked separately from service silence." />
      {agents.length === 0 ? (
        <p className="text-ink-muted text-sm">{t("common.no_data")}</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((a) => (
            <div key={a.id} className="acrylic rounded-win p-4 flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="font-medium truncate">{a.host_id}</span>
                <span className={`text-xs px-2 py-1 rounded-win ${statusColor[a.status]}`}>{a.status}</span>
              </div>
              <div className="text-xs text-ink-muted grid grid-cols-2 gap-1">
                <span>CPU: {a.cpu_percent.toFixed(1)}%</span>
                <span>Mem: {a.memory_mb.toFixed(0)} MB</span>
                <span>Queue: {a.queue_depth}</span>
                <span>Dropped: {a.dropped_events_total}</span>
              </div>
              <div className="text-xs text-ink-muted">
                Last seen: {a.last_seen_at ? new Date(a.last_seen_at).toLocaleString() : "never"}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
