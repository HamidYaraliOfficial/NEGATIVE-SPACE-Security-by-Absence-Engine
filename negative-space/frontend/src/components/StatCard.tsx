export function StatCard({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string | number;
  tone?: "default" | "danger" | "warn" | "ok";
}) {
  const toneColor =
    tone === "danger" ? "text-danger" : tone === "warn" ? "text-warn" : tone === "ok" ? "text-ok" : "text-ink";
  return (
    <div className="acrylic rounded-win p-5 flex flex-col gap-2 min-w-[160px]">
      <span className="text-xs uppercase tracking-wide text-ink-muted">{label}</span>
      <span className={`text-3xl font-semibold ${toneColor}`}>{value}</span>
    </div>
  );
}
