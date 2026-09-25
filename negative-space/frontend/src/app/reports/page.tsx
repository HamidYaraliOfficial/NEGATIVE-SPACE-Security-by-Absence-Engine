"use client";

import { useEffect, useState } from "react";
import { TopBar } from "@/components/TopBar";
import { useI18n } from "@/i18n/I18nProvider";
import { api } from "@/lib/api";
import { PostureSummary } from "@/lib/types";

export default function ReportsPage() {
  const { t } = useI18n();
  const [summary, setSummary] = useState<PostureSummary | null>(null);

  useEffect(() => {
    api.postureSummary().then((s) => setSummary(s as PostureSummary)).catch(() => {});
  }, []);

  const download = (format: "json" | "csv") => {
    if (!summary) return;
    let content = "";
    let mime = "application/json";
    if (format === "json") {
      content = JSON.stringify(summary, null, 2);
    } else {
      mime = "text/csv";
      content = Object.entries(summary).map(([k, v]) => `${k},${v}`).join("\n");
    }
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `negative-space-posture-report.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="px-4">
      <TopBar title={t("nav.reports")} subtitle="Export posture, detection and agent-health summaries." />
      <div className="acrylic rounded-win p-5 flex flex-col gap-3 max-w-md">
        <p className="text-sm text-ink-muted">Security posture snapshot, ready to export.</p>
        <div className="flex gap-2">
          <button onClick={() => download("json")} className="focus-ring rounded-win px-4 py-2 text-sm bg-accent text-accent-fg">
            Export JSON
          </button>
          <button onClick={() => download("csv")} className="focus-ring rounded-win px-4 py-2 text-sm border border-border">
            Export CSV
          </button>
        </div>
      </div>
    </div>
  );
}
