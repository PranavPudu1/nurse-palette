export type ShiftType = "D" | "N" | "X";

export interface Nurse {
  id: string;
  name: string;
}

export interface ScheduleData {
  [nurseId: string]: {
    [dateKey: string]: ShiftType; // dateKey = "YYYY-MM-DD"
  };
}

const NAMES = [
  "Ava Patel",
  "Mia Johnson",
  "Sofia Garcia",
  "Emily Chen",
  "Olivia Kim",
  "Harper Nguyen",
  "Isabella Martinez",
  "Charlotte Brown",
];

const SHIFT_OPTIONS: ShiftType[] = ["D", "N", "X"];

function randomShift(): ShiftType {
  const r = Math.random();
  if (r < 0.4) return "D";
  if (r < 0.7) return "N";
  return "X";
}

export function createInitialNurses(): Nurse[] {
  return NAMES.map((name, i) => ({ id: `nurse-${i}`, name }));
}

export function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate();
}

export function generateSchedule(
  nurses: Nurse[],
  year: number,
  month: number
): ScheduleData {
  const days = getDaysInMonth(year, month);
  const schedule: ScheduleData = {};
  for (const nurse of nurses) {
    schedule[nurse.id] = {};
    for (let d = 1; d <= days; d++) {
      const key = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      schedule[nurse.id][key] = randomShift();
    }
  }
  return schedule;
}

export function cycleShift(current: ShiftType): ShiftType {
  const idx = SHIFT_OPTIONS.indexOf(current);
  return SHIFT_OPTIONS[(idx + 1) % SHIFT_OPTIONS.length];
}

export function dateKey(year: number, month: number, day: number): string {
  return `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}
