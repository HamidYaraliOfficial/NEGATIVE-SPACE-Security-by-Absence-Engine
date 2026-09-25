"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import en from "./en.json";
import fa from "./fa.json";
import zh from "./zh.json";

const DICTS = { en, fa, zh } as const;
export type Lang = keyof typeof DICTS;

interface I18nCtx {
  lang: Lang;
  dir: "ltr" | "rtl";
  t: (path: string) => string;
  setLang: (l: Lang) => void;
}

const Ctx = createContext<I18nCtx | null>(null);

function resolve(obj: any, path: string): string {
  const parts = path.split(".");
  let cur = obj;
  for (const p of parts) {
    if (cur == null) return path;
    cur = cur[p];
  }
  return typeof cur === "string" ? cur : path;
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem("ns-lang") as Lang | null;
      if (stored && DICTS[stored]) setLangState(stored);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    const dict = DICTS[lang];
    document.documentElement.lang = lang;
    document.documentElement.dir = dict.dir as "ltr" | "rtl";
    try {
      window.localStorage.setItem("ns-lang", lang);
    } catch {
      /* ignore */
    }
  }, [lang]);

  const t = (path: string) => resolve(DICTS[lang], path);
  const setLang = (l: Lang) => setLangState(l);

  return (
    <Ctx.Provider value={{ lang, dir: DICTS[lang].dir as "ltr" | "rtl", t, setLang }}>
      {children}
    </Ctx.Provider>
  );
}

export function useI18n() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
