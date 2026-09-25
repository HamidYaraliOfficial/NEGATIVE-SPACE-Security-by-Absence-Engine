"use client";

import { useEffect, useState } from "react";
import { TopBar } from "@/components/TopBar";
import { StatCard } from "@/components/StatCard";
import { useI18n } from "@/i18n/I18nProvider";
import { api } from "@/lib/api";
import { PostureSummary } from "@/lib/types";

export default function OverviewPage() {
  const { t } = useI18n();
  const [summary, setSummary] = useState<PostureSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .postureSummary()
      .then((s) => setSummary(s as PostureSummary))
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div className="px-4">
      <TopBar title={t("overview.title")} subtitle={t("overview.subtitle")} />

      {error && (
        <div className="acrylic rounded-win p-4 mx-0 mb-6 text-sm text-danger">
          {error} — is the backend running at NEXT_PUBLIC_API_URL and are you logged in?
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label={t("overview.open_detections")} value={summary?.open_detections ?? "—"} />
        <StatCard
          label={t("overview.critical_open")}
          value={summary?.critical_open_detections ?? "—"}
          tone="danger"
        />
        <StatCard label={t("overview.detections_24h")} value={summary?.detections_last_24h ?? "—"} />
        <StatCard label={t("overview.active_incidents")} value={summary?.active_incidents ?? "—"} tone="warn" />
        <StatCard
          label={t("overview.agents_online")}
          value={summary ? `${summary.agents_online}/${summary.agents_total}` : "—"}
          tone="ok"
        />
        <StatCard
          label={t("overview.blind_spot_ratio")}
          value={summary ? `${Math.round(summary.blind_spot_ratio * 100)}%` : "—"}
          tone={summary && summary.blind_spot_ratio > 0.2 ? "danger" : "default"}
        />
        <StatCard label={t("overview.missing_relationships")} value={summary?.missing_relationships ?? "—"} />
        <StatCard label="Entities" value={summary?.entity_count ?? "—"} />
      </div>
    </div>
  );
}
