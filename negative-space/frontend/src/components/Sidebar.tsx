"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useI18n } from "@/i18n/I18nProvider";

const NAV_ITEMS: { href: string; key: string }[] = [
  { href: "/", key: "overview" },
  { href: "/silence-explorer", key: "silence_explorer" },
  { href: "/relationship-graph", key: "relationship_graph" },
  { href: "/incidents", key: "incident_center" },
  { href: "/agents", key: "agent_management" },
  { href: "/business-hours", key: "business_hours" },
  { href: "/reports", key: "reports" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { t } = useI18n();

  return (
    <aside className="acrylic w-64 shrink-0 h-screen sticky top-0 flex flex-col p-4 gap-1">
      <div className="px-2 py-3 mb-2">
        <div className="text-lg font-semibold tracking-tight">{t("app_name")}</div>
        <div className="text-xs text-ink-muted">{t("app_tagline")}</div>
      </div>
      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`focus-ring rounded-win px-3 py-2 text-sm transition-colors ${
                active ? "bg-accent text-accent-fg" : "text-ink hover:bg-surface-alt"
              }`}
            >
              {t(`nav.${item.key}`)}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
