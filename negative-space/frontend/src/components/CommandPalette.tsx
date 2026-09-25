"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useI18n } from "@/i18n/I18nProvider";

interface Command {
  id: string;
  label: string;
  href: string;
}

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const router = useRouter();
  const { t } = useI18n();

  const commands: Command[] = [
    { id: "overview", label: t("nav.overview"), href: "/" },
    { id: "silence", label: t("nav.silence_explorer"), href: "/silence-explorer" },
    { id: "graph", label: t("nav.relationship_graph"), href: "/relationship-graph" },
    { id: "incidents", label: t("nav.incident_center"), href: "/incidents" },
    { id: "agents", label: t("nav.agent_management"), href: "/agents" },
    { id: "business_hours", label: t("nav.business_hours"), href: "/business-hours" },
    { id: "reports", label: t("nav.reports"), href: "/reports" },
  ];

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  if (!open) return null;

  const filtered = commands.filter((c) => c.label.toLowerCase().includes(query.toLowerCase()));

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-32 bg-black/40"
      onClick={() => setOpen(false)}
    >
      <div
        className="acrylic w-full max-w-lg rounded-win shadow-acrylic overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <input
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t("common.search_placeholder")}
          className="w-full px-4 py-3 bg-transparent outline-none border-b border-border text-sm"
        />
        <div className="max-h-72 overflow-y-auto">
          {filtered.map((c) => (
            <button
              key={c.id}
              onClick={() => {
                router.push(c.href);
                setOpen(false);
                setQuery("");
              }}
              className="w-full text-start px-4 py-2.5 text-sm hover:bg-surface-alt focus-ring"
            >
              {c.label}
            </button>
          ))}
          {filtered.length === 0 && (
            <div className="px-4 py-6 text-sm text-ink-muted text-center">{t("common.no_data")}</div>
          )}
        </div>
      </div>
    </div>
  );
}
