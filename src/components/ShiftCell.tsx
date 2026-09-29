import { ShiftType } from "@/lib/scheduler-data";
import type { TimeOffStatus } from "@/lib/time-off";

interface ShiftCellProps {
  value: ShiftType;
  onClick?: () => void;
  onContextMenu?: (e: React.MouseEvent) => void;
  readOnly?: boolean;
  /** Set when the nurse has time off on this day. */
  timeOff?: TimeOffStatus;
  /** True when the day falls outside a temp nurse's contract window. */
  outsideWindow?: boolean;
  label?: string;
}

export function ShiftCell({
  value,
  onClick,
  onContextMenu,
  readOnly,
  timeOff,
  outsideWindow,
  label,
}: ShiftCellProps) {
  const base =
    "w-9 h-9 flex items-center justify-center text-xs font-semibold rounded select-none transition-colors duration-100 border";

  const colors: Record<ShiftType, string> = {
    D: "bg-shift-day text-shift-day-foreground border-shift-day/60",
    E: "bg-shift-evening text-shift-evening-foreground border-shift-evening/60",
    N: "bg-shift-night text-shift-night-foreground border-shift-night/60",
    X: "bg-shift-off text-shift-off-foreground border-transparent",
  };

  // An unworked day that the nurse has time off on shows "O", not "X". X used to
  // mean both "nothing assigned" and "asked for this day off", which is exactly
  // the ambiguity raised in review.
  const isTimeOffDay = !!timeOff && value === "X";
  const shown = isTimeOffDay ? "O" : value;
  const tone = isTimeOffDay
    ? "bg-shift-timeoff text-shift-timeoff-foreground border-transparent"
    : colors[value];
  const muted = outsideWindow && value === "X" ? "opacity-40" : "";

  return (
    <button
      type="button"
      className={`${base} ${tone} ${muted} ${readOnly ? "cursor-default" : "cursor-pointer hover:opacity-80 active:scale-95"}`}
      onClick={readOnly ? undefined : onClick}
      onContextMenu={readOnly ? undefined : onContextMenu}
      disabled={readOnly}
      aria-label={label ?? `Shift: ${shown}`}
    >
      {shown}
    </button>
  );
}
