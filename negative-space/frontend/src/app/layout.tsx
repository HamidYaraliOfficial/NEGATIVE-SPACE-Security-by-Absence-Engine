import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import { I18nProvider } from "@/i18n/I18nProvider";
import { Sidebar } from "@/components/Sidebar";
import { CommandPalette } from "@/components/CommandPalette";

export const metadata: Metadata = {
  title: "NEGATIVE SPACE — Security by Absence Engine",
  description: "Detects what should have happened, but didn't.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="dark" data-accent="blue" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <I18nProvider>
            <div className="flex min-h-screen">
              <Sidebar />
              <main className="flex-1 pb-10">{children}</main>
            </div>
            <CommandPalette />
          </I18nProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
