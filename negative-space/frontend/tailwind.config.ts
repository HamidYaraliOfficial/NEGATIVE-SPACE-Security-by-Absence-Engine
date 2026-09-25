import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "var(--ns-surface)",
        "surface-alt": "var(--ns-surface-alt)",
        border: "var(--ns-border)",
        accent: "var(--ns-accent)",
        "accent-fg": "var(--ns-accent-fg)",
        ink: "var(--ns-ink)",
        "ink-muted": "var(--ns-ink-muted)",
        danger: "var(--ns-danger)",
        warn: "var(--ns-warn)",
        ok: "var(--ns-ok)",
      },
      borderRadius: {
        win: "8px",
      },
      fontFamily: {
        sans: ["var(--ns-font)", "sans-serif"],
      },
      boxShadow: {
        acrylic: "0 8px 32px rgba(0,0,0,0.18)",
      },
    },
  },
  plugins: [],
};
export default config;
