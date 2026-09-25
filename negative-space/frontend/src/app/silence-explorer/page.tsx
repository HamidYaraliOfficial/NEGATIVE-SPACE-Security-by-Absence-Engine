"use client";

import { useEffect, useState } from "react";
import { TopBar } from "@/components/TopBar";
import { SilenceTable } from "@/components/SilenceTable";
import { useI18n } from "@/i18n/I18nProvider";
import { api } from "@/lib/api";
import { Detection } from "@/lib/types";

export default function SilenceExplorerPage() {
  const { t } = useI18n();
  const [detections, setDetections] = useState<Detection[]>([]);
  const [busy, setBusy] = useState(false);

  const load = () => {
    api
      .listDetections()
      .then((d) => setDetections(d as Detection[]))
      .catch(() => setDetections([]));
  };

  useEffect(load, []);

  const sweep = async () => {
    setBusy(true);
    try {
      await api.triggerSweep();
      load();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="px-4">
      <TopBar title={t("nav.silence_explorer")} subtitle="Every place expected reality and observed reality have diverged." />
      <div className="mb-4">
        <button
          onClick={sweep}
          disabled={busy}
          className="focus-ring rounded-win px-4 py-2 text-sm bg-accent text-accent-fg disabled:opacity-50"
        >
          {busy ? t("common.loading") : "Run detection sweep now"}
        </button>
      </div>
      <SilenceTable detections={detections} />
    </div>
  );
}
