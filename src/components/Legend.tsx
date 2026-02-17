import { ShiftType } from "@/lib/scheduler-data";

export function Legend() {
  const items: { type: ShiftType; label: string; cls: string }[] = [
    { type: "D", label: "Day", cls: "bg-shift-day text-shift-day-foreground" },
    { type: "N", label: "Night", cls: "bg-shift-night text-shift-night-foreground" },
    { type: "X", label: "Off", cls: "bg-shift-off text-shift-off-foreground" },
  ];

  return (
    <div className="flex items-center gap-4 text-sm">
      {items.map((item) => (
        <div key={item.type} className="flex items-center gap-1.5">
          <span
            className={`inline-flex items-center justify-center w-6 h-6 rounded text-xs font-semibold ${item.cls}`}
          >
            {item.type}
          </span>
          <span className="text-muted-foreground">{item.label}</span>
        </div>
      ))}
    </div>
  );
}
