"use client";

import { useState } from "react";
import { useI18n, Lang } from "@/i18n/I18nProvider";
import { useTheme, ThemeMode, ThemeAccent } from "@/components/ThemeProvider";

export function TopBar({ title, subtitle }: { title: string; subtitle?: string }) {
  const { t, lang, setLang } = useI18n();
  const { mode, accent, setMode, setAccent } = useTheme();
  const [openSettings, setOpenSettings] = useState(false);

  return (
    <header className="acrylic sticky top-0 z-10 rounded-win mx-4 mt-4 mb-6 px-5 py-4 flex items-center justify-between">
      <div>
        <h1 className="text-xl font-semibold">{title}</h1>
        {subtitle && <p className="text-sm text-ink-muted mt-0.5">{subtitle}</p>}
      </div>

      <div className="relative">
        <button
          onClick={() => setOpenSettings((v) => !v)}
          className="focus-ring rounded-win px-3 py-2 text-sm border border-border hover:bg-surface-alt"
        >
          {t("common.theme")}
        </button>
        {openSettings && (
          <div className="acrylic absolute end-0 mt-2 w-64 rounded-win p-3 shadow-acrylic flex flex-col gap-3">
            <div>
              <div className="text-xs text-ink-muted mb-1">{t("common.language")}</div>
              <div className="flex gap-1">
                {(["en", "fa", "zh"] as Lang[]).map((l) => (
                  <button
                    key={l}
                    onClick={() => setLang(l)}
                    className={`flex-1 rounded-win px-2 py-1 text-xs border border-border ${
                      lang === l ? "bg-accent text-accent-fg" : "hover:bg-surface-alt"
                    }`}
                  >
                    {l.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <div className="text-xs text-ink-muted mb-1">{t("common.theme")}</div>
              <div className="flex gap-1">
                {(["light", "dark", "amoled"] as ThemeMode[]).map((m) => (
                  <button
                    key={m}
                    onClick={() => setMode(m)}
                    className={`flex-1 rounded-win px-2 py-1 text-xs border border-border ${
                      mode === m ? "bg-accent text-accent-fg" : "hover:bg-surface-alt"
                    }`}
                  >
                    {t(`common.${m}`)}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <div className="text-xs text-ink-muted mb-1">{t("common.accent")}</div>
              <div className="flex gap-1">
                {(["blue", "red"] as ThemeAccent[]).map((a) => (
                  <button
                    key={a}
                    onClick={() => setAccent(a)}
                    className={`flex-1 rounded-win px-2 py-1 text-xs border border-border ${
                      accent === a ? "bg-accent text-accent-fg" : "hover:bg-surface-alt"
                    }`}
                  >
                    {t(`common.${a}`)}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
