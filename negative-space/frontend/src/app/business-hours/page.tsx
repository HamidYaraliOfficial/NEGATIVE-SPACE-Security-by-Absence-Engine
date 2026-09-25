"use client";

import { useEffect, useState } from "react";
import { TopBar } from "@/components/TopBar";
import { useI18n } from "@/i18n/I18nProvider";
import { api } from "@/lib/api";
import { BusinessHoursRow, BusinessHoursStatus } from "@/lib/types";

const DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"] as const;

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function StatusBadge({ id }: { id: string }) {
  const { t } = useI18n();
  const [status, setStatus] = useState<BusinessHoursStatus | null>(null);

  useEffect(() => {
    const load = () => api.businessHoursStatus(id).then((s) => setStatus(s as BusinessHoursStatus)).catch(() => {});
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, [id]);

  if (!status) return <span className="text-xs text-ink-muted">{t("common.loading")}</span>;

  if (status.is_open) {
    return (
      <span className="text-xs px-2 py-1 rounded-win bg-ok/15 text-ok">
        {t("common.open")} ({status.current_window?.[0]}–{status.current_window?.[1]})
      </span>
    );
  }
  return (
    <span className="text-xs px-2 py-1 rounded-win bg-danger/15 text-danger">
      {t("common.closed")} · {t("common.next_open")}{" "}
      {status.next_open_at ? new Date(status.next_open_at).toLocaleString() : "—"}
      {status.seconds_until_next_open != null &&
        ` (${t("common.in")} ${formatDuration(status.seconds_until_next_open)})`}
      {status.next_window_duration_seconds != null &&
        ` · ${t("common.duration")}: ${formatDuration(status.next_window_duration_seconds)}`}
    </span>
  );
}

export default function BusinessHoursPage() {
  const { t } = useI18n();
  const [rows, setRows] = useState<BusinessHoursRow[]>([]);
  const [name, setName] = useState("");
  const [timezone, setTimezone] = useState("UTC");
  const [isMaintenance, setIsMaintenance] = useState(false);
  const [schedule, setSchedule] = useState<Record<string, [string, string][]>>(
    Object.fromEntries(DAYS.map((d) => [d, d === "sat" || d === "sun" ? [] : [["09:00", "18:00"]]]))
  );

  const load = () => api.listBusinessHours().then((r) => setRows(r as BusinessHoursRow[])).catch(() => {});
  useEffect(load, []);

  const toggleDay = (day: string) => {
    setSchedule((prev) => ({
      ...prev,
      [day]: prev[day] && prev[day].length > 0 ? [] : [["09:00", "18:00"]],
    }));
  };

  const updateWindow = (day: string, idx: 0 | 1, value: string) => {
    setSchedule((prev) => {
      const windows = prev[day] && prev[day].length > 0 ? [...prev[day]] : [["09:00", "18:00"]];
      const win: [string, string] = [...windows[0]] as [string, string];
      win[idx] = value;
      return { ...prev, [day]: [win] };
    });
  };

  const create = async () => {
    if (!name.trim()) return;
    await api.createBusinessHours({
      name,
      timezone,
      schedule,
      is_maintenance_window: isMaintenance,
    });
    setName("");
    load();
  };

  const remove = async (id: string) => {
    await api.deleteBusinessHours(id);
    load();
  };

  return (
    <div className="px-4">
      <TopBar title={t("business_hours.title")} subtitle={t("business_hours.subtitle")} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="acrylic rounded-win p-5 flex flex-col gap-4">
          <div>
            <label className="text-xs text-ink-muted block mb-1">{t("business_hours.name")}</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-win border border-border bg-transparent px-3 py-2 text-sm focus-ring"
              placeholder="e.g. Payments API"
            />
          </div>
          <div>
            <label className="text-xs text-ink-muted block mb-1">{t("business_hours.timezone")}</label>
            <input
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="w-full rounded-win border border-border bg-transparent px-3 py-2 text-sm focus-ring"
              placeholder="UTC / Asia/Tehran / Asia/Shanghai"
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={isMaintenance} onChange={(e) => setIsMaintenance(e.target.checked)} />
            {t("business_hours.maintenance_window")}
          </label>

          <div>
            <div className="text-xs text-ink-muted mb-2">{t("business_hours.schedule")}</div>
            <div className="flex flex-col gap-2">
              {DAYS.map((d) => {
                const active = schedule[d] && schedule[d].length > 0;
                return (
                  <div key={d} className="flex items-center gap-2">
                    <button
                      onClick={() => toggleDay(d)}
                      className={`w-16 rounded-win px-2 py-1 text-xs border border-border ${
                        active ? "bg-accent text-accent-fg" : "text-ink-muted"
                      }`}
                    >
                      {t(`business_hours.${d}`)}
                    </button>
                    {active && (
                      <>
                        <input
                          type="time"
                          value={schedule[d][0][0]}
                          onChange={(e) => updateWindow(d, 0, e.target.value)}
                          className="rounded-win border border-border bg-transparent px-2 py-1 text-xs"
                        />
                        <span className="text-ink-muted text-xs">–</span>
                        <input
                          type="time"
                          value={schedule[d][0][1]}
                          onChange={(e) => updateWindow(d, 1, e.target.value)}
                          className="rounded-win border border-border bg-transparent px-2 py-1 text-xs"
                        />
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <button
            onClick={create}
            className="focus-ring self-start rounded-win px-4 py-2 text-sm bg-accent text-accent-fg"
          >
            {t("business_hours.create")}
          </button>
        </div>

        <div className="flex flex-col gap-3">
          {rows.length === 0 && <p className="text-ink-muted text-sm">{t("common.no_data")}</p>}
          {rows.map((r) => (
            <div key={r.id} className="acrylic rounded-win p-4 flex items-center justify-between gap-3">
              <div>
                <div className="font-medium">{r.name}</div>
                <div className="text-xs text-ink-muted">{r.timezone}{r.is_maintenance_window ? " · maintenance" : ""}</div>
                <div className="mt-1">
                  <StatusBadge id={r.id} />
                </div>
              </div>
              <button onClick={() => remove(r.id)} className="text-xs text-danger hover:underline focus-ring">
                {t("common.delete")}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
