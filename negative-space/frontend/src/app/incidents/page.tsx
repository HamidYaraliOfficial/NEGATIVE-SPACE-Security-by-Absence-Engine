"use client";

import { useEffect, useState } from "react";
import { TopBar } from "@/components/TopBar";
import { useI18n } from "@/i18n/I18nProvider";
import { api } from "@/lib/api";

interface CaseRow {
  id: string;
  title: string;
  status: string;
  priority: string;
  owner: string;
  created_at: string;
}

export default function IncidentsPage() {
  const { t } = useI18n();
  const [cases, setCases] = useState<CaseRow[]>([]);
  const [title, setTitle] = useState("");

  const load = () => api.listCases().then((c) => setCases(c as CaseRow[])).catch(() => {});
  useEffect(load, []);

  const create = async () => {
    if (!title.trim()) return;
    await api.createCase({ title, priority: "medium", tags: [] });
    setTitle("");
    load();
  };

  return (
    <div className="px-4">
      <TopBar title={t("nav.incident_center")} subtitle="Compound silences, reconstructed timelines, and open cases." />

      <div className="acrylic rounded-win p-4 mb-6 flex gap-2">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="New case title..."
          className="flex-1 rounded-win border border-border bg-transparent px-3 py-2 text-sm focus-ring"
        />
        <button onClick={create} className="focus-ring rounded-win px-4 py-2 text-sm bg-accent text-accent-fg">
          {t("common.add")}
        </button>
      </div>

      {cases.length === 0 ? (
        <p className="text-ink-muted text-sm">{t("common.no_data")}</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {cases.map((c) => (
            <div key={c.id} className="acrylic rounded-win p-4">
              <div className="flex items-center justify-between">
                <span className="font-medium">{c.title}</span>
                <span className="text-xs px-2 py-1 rounded-win bg-surface-alt">{c.status}</span>
              </div>
              <div className="text-xs text-ink-muted mt-1">
                Priority: {c.priority} · Owner: {c.owner || "unassigned"}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
