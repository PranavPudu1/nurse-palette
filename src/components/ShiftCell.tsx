import { ShiftType } from "@/lib/scheduler-data";

interface ShiftCellProps {
  value: ShiftType;
  onClick?: () => void;
  onContextMenu?: (e: React.MouseEvent) => void;
  readOnly?: boolean;
}

export function ShiftCell({ value, onClick, onContextMenu, readOnly }: ShiftCellProps) {
  const base =
    "w-9 h-9 flex items-center justify-center text-xs font-semibold rounded select-none transition-colors duration-100 border";

  const colors: Record<ShiftType, string> = {
    D: "bg-shift-day text-shift-day-foreground border-shift-day/60",
    E: "bg-shift-evening text-shift-evening-foreground border-shift-evening/60",
    N: "bg-shift-night text-shift-night-foreground border-shift-night/60",
    X: "bg-shift-off text-shift-off-foreground border-transparent",
  };

  return (
    <button
      type="button"
      className={`${base} ${colors[value]} ${readOnly ? "cursor-default" : "cursor-pointer hover:opacity-80 active:scale-95"}`}
      onClick={readOnly ? undefined : onClick}
      onContextMenu={readOnly ? undefined : onContextMenu}
      disabled={readOnly}
      aria-label={`Shift: ${value}`}
    >
      {value}
    </button>
  );
}
