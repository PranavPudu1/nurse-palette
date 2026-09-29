import { useLang } from "@/lib/i18n";

export function Legend() {
  const { t } = useLang();
  // Typed as a plain symbol rather than ShiftType: "O" marks time off, which is
  // an absence, not a shift, and ShiftType is the database CHECK on
  // schedules.shift_type.
  const items: { symbol: string; label: string; cls: string }[] = [
    { symbol: "D", label: t("shift.D"), cls: "bg-shift-day text-shift-day-foreground" },
    { symbol: "E", label: t("shift.E"), cls: "bg-shift-evening text-shift-evening-foreground" },
    { symbol: "N", label: t("shift.N"), cls: "bg-shift-night text-shift-night-foreground" },
    { symbol: "X", label: t("shift.X"), cls: "bg-shift-off text-shift-off-foreground" },
    { symbol: "O", label: t("shift.O.approved"), cls: "bg-shift-timeoff text-shift-timeoff-foreground" },
  ];

  return (
    <div className="flex items-center gap-4 text-sm flex-wrap">
      {items.map((item) => (
        <div key={item.symbol} className="flex items-center gap-1.5">
          <span
            className={`inline-flex items-center justify-center w-6 h-6 rounded text-xs font-semibold ${item.cls}`}
          >
            {item.symbol}
          </span>
          <span className="text-muted-foreground">{item.label}</span>
        </div>
      ))}
      {/* The line style is what separates a request from a decision, so it needs
          its own legend entry rather than living only in the cells. */}
      <div className="flex items-center gap-1.5">
        <span className="inline-block w-6 h-6 rounded border-2 border-dashed border-shift-timeoff-foreground/60" />
        <span className="text-muted-foreground">{t("legend.ptoPending")}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <span className="inline-block w-6 h-6 rounded border-2 border-solid border-shift-timeoff-foreground" />
        <span className="text-muted-foreground">{t("legend.ptoApproved")}</span>
      </div>
    </div>
  );
}
