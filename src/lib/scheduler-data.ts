export type ShiftType = "D" | "E" | "N" | "X";

export interface Nurse {
  id: string;
  name: string;
}

export interface ScheduleData {
  [nurseId: string]: {
    [dateKey: string]: ShiftType; // dateKey = "YYYY-MM-DD"
  };
}

const SHIFT_OPTIONS: ShiftType[] = ["X", "D", "E", "N"];

export function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate();
}

export function cycleShift(current: ShiftType): ShiftType {
  const idx = SHIFT_OPTIONS.indexOf(current);
  return SHIFT_OPTIONS[(idx + 1) % SHIFT_OPTIONS.length];
}

export function dateKey(year: number, month: number, day: number): string {
  return `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}
