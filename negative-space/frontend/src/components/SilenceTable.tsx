"use client";

import { Detection } from "@/lib/types";
import { useI18n } from "@/i18n/I18nProvider";

const severityColor: Record<string, string> = {
  critical: "bg-danger/15 text-danger",
  high: "bg-warn/15 text-warn",
  medium: "bg-accent/15 text-accent",
  low: "bg-ink-muted/15 text-ink-muted",
};

export function SilenceTable({ detections }: { detections: Detection[] }) {
  const { t } = useI18n();

  if (detections.length === 0) {
    return <p className="text-ink-muted text-sm py-8 text-center">{t("common.no_data")}</p>;
  }

  return (
    <div className="acrylic rounded-win overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-ink-muted text-xs uppercase tracking-wide">
            <th className="text-start px-4 py-3">{t("common.category")}</th>
            <th className="text-start px-4 py-3">{t("common.severity")}</th>
            <th className="text-start px-4 py-3">{t("common.confidence")}</th>
            <th className="text-start px-4 py-3">{t("common.since")}</th>
            <th className="text-start px-4 py-3">{t("common.status")}</th>
          </tr>
        </thead>
        <tbody>
          {detections.map((d) => (
            <tr key={d.id} className="border-b border-border last:border-0 hover:bg-surface-alt transition-colors">
              <td className="px-4 py-3 font-medium">{d.category.replace(/_/g, " ")}</td>
              <td className="px-4 py-3">
                <span className={`px-2 py-1 rounded-win text-xs font-medium ${severityColor[d.severity] ?? ""}`}>
                  {d.severity}
                </span>
              </td>
              <td className="px-4 py-3">{Math.round(d.confidence * 100)}%</td>
              <td className="px-4 py-3 text-ink-muted">{new Date(d.silence_started_at).toLocaleString()}</td>
              <td className="px-4 py-3 text-ink-muted">{d.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
