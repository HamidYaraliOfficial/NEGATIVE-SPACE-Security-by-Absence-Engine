"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";

export type ThemeMode = "light" | "dark" | "amoled";
export type ThemeAccent = "blue" | "red";

interface ThemeCtx {
  mode: ThemeMode;
  accent: ThemeAccent;
  setMode: (m: ThemeMode) => void;
  setAccent: (a: ThemeAccent) => void;
}

const Ctx = createContext<ThemeCtx | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>("dark");
  const [accent, setAccentState] = useState<ThemeAccent>("blue");

  useEffect(() => {
    try {
      const storedMode = window.localStorage.getItem("ns-theme-mode") as ThemeMode | null;
      const storedAccent = window.localStorage.getItem("ns-theme-accent") as ThemeAccent | null;
      if (storedMode) setModeState(storedMode);
      if (storedAccent) setAccentState(storedAccent);
    } catch {
      // localStorage unavailable — fall back to defaults silently.
    }
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", mode);
    document.documentElement.setAttribute("data-accent", accent);
    try {
      window.localStorage.setItem("ns-theme-mode", mode);
      window.localStorage.setItem("ns-theme-accent", accent);
    } catch {
      /* ignore */
    }
  }, [mode, accent]);

  const setMode = (m: ThemeMode) => setModeState(m);
  const setAccent = (a: ThemeAccent) => setAccentState(a);

  return <Ctx.Provider value={{ mode, accent, setMode, setAccent }}>{children}</Ctx.Provider>;
}

export function useTheme() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
