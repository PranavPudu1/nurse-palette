import type { ShiftType, ScheduleData, Nurse } from "./scheduler-data";
import { getDaysInMonth, dateKey } from "./scheduler-data";

export interface Violation {
  nurseId: string;
  date: string;
  rule: string;
  severity: "error" | "warning";
  message: string;
}

export interface WardConfig {
  shift_type: string;
  required_nurses: number;
  level_mix: Record<string, number>;
}

export interface NurseWithLevel extends Nurse {
  level: number;
}

/**
 * Validate all hard constraints for a schedule and return violations.
 */
export function validateSchedule(
  nurses: NurseWithLevel[],
  schedule: ScheduleData,
  year: number,
  month: number,
  wardConfigs: WardConfig[],
  exclusions: { nurse_id_1: string; nurse_id_2: string }[] = []
): Violation[] {
  const violations: Violation[] = [];
  const days = getDaysInMonth(year, month);

  for (const nurse of nurses) {
    const nurseSchedule = schedule[nurse.id] || {};
    validateNightShiftRule(nurse, nurseSchedule, year, month, days, violations);
    validateConsecutiveDaysRule(nurse, nurseSchedule, year, month, days, violations);
    validateOvertimeRule(nurse, nurseSchedule, year, month, days, violations);
  }

  // Staffing requirements per day
  validateStaffingRequirements(nurses, schedule, year, month, days, wardConfigs, violations);

  // Exclusion pairs
  validateExclusions(nurses, schedule, year, month, days, exclusions, violations);

  return violations;
}

function getShift(nurseSchedule: Record<string, ShiftType>, year: number, month: number, day: number): ShiftType {
  return nurseSchedule[dateKey(year, month, day)] ?? "X";
}

/**
 * Night=2 consecutive + 2 mandatory off after
 */
function validateNightShiftRule(
  nurse: NurseWithLevel,
  nurseSchedule: Record<string, ShiftType>,
  year: number,
  month: number,
  days: number,
  violations: Violation[]
) {
  for (let d = 1; d <= days; d++) {
    const shift = getShift(nurseSchedule, year, month, d);
    if (shift !== "N") continue;

    // Check: if this is a single night (prev != N and next != N), that's a violation
    const prevShift = d > 1 ? getShift(nurseSchedule, year, month, d - 1) : "X";
    const nextShift = d < days ? getShift(nurseSchedule, year, month, d + 1) : "X";

    if (prevShift !== "N" && nextShift !== "N") {
      violations.push({
        nurseId: nurse.id,
        date: dateKey(year, month, d),
        rule: "night-pair",
        severity: "error",
        message: `${nurse.name} has a single night shift on day ${d}. Night shifts must come in consecutive pairs (2 nights in a row). Fix: add a night shift on day ${d > 1 ? d - 1 : d + 1} or remove this one.`,
      });
    }

    // Check: after a pair of nights, the next 2 days must be off
    if (prevShift === "N" && shift === "N") {
      // This is the second night in a pair - check the 2 days after
      for (let off = 1; off <= 2; off++) {
        const offDay = d + off;
        if (offDay <= days) {
          const offShift = getShift(nurseSchedule, year, month, offDay);
          if (offShift !== "X") {
            violations.push({
              nurseId: nurse.id,
              date: dateKey(year, month, offDay),
              rule: "night-rest",
              severity: "error",
              message: `${nurse.name} is working on day ${offDay} but needs rest. After a night pair (days ${d - 1}–${d}), the next 2 days must be off. Fix: clear the shift on day ${offDay}.`,
            });
          }
        }
      }
    }
  }
}

/**
 * Max 4 consecutive working days, then at least 2 off
 */
function validateConsecutiveDaysRule(
  nurse: NurseWithLevel,
  nurseSchedule: Record<string, ShiftType>,
  year: number,
  month: number,
  days: number,
  violations: Violation[]
) {
  let consecutive = 0;
  for (let d = 1; d <= days; d++) {
    const shift = getShift(nurseSchedule, year, month, d);
    if (shift !== "X") {
      consecutive++;
      if (consecutive > 4) {
        violations.push({
          nurseId: nurse.id,
          date: dateKey(year, month, d),
          rule: "max-consecutive",
          severity: "error",
          message: `${nurse.name} has been working ${consecutive} days straight (max is 4). Fix: give them a day off on or before day ${d}.`,
        });
      }
    } else {
      // Check if after a stretch of 3-4 days, we need 2 off
      if (consecutive >= 3) {
        const nextDay = d + 1;
        if (nextDay <= days) {
          const nextShift = getShift(nurseSchedule, year, month, nextDay);
          if (nextShift !== "X") {
            violations.push({
              nurseId: nurse.id,
              date: dateKey(year, month, d),
              rule: "rest-after-streak",
              severity: "warning",
              message: `${nurse.name} worked ${consecutive} days in a row and only has 1 day off. Recommended: give 2 consecutive days off after a streak of 3+ workdays.`,
            });
          }
        }
      }
      consecutive = 0;
    }
  }
}

/**
 * Overtime: more than 40 hours per week (5 shifts × 8h = 40h)
 */
function validateOvertimeRule(
  nurse: NurseWithLevel,
  nurseSchedule: Record<string, ShiftType>,
  year: number,
  month: number,
  days: number,
  violations: Violation[]
) {
  // Check each ISO week in the month
  for (let d = 1; d <= days; d++) {
    const date = new Date(year, month, d);
    if (date.getDay() === 1 || d === 1) {
      // Start of week - count shifts this week
      let weekShifts = 0;
      for (let wd = d; wd < d + 7 && wd <= days; wd++) {
        const shift = getShift(nurseSchedule, year, month, wd);
        if (shift !== "X") weekShifts++;
      }
      if (weekShifts > 5) {
        violations.push({
          nurseId: nurse.id,
          date: dateKey(year, month, d),
          rule: "overtime",
          severity: "warning",
          message: `${nurse.name} has ${weekShifts} shifts in the week starting day ${d} (max 5 before overtime). Fix: remove ${weekShifts - 5} shift(s) this week to stay within 40 hours.`,
        });
      }
    }
  }
}

/**
 * Check staffing requirements per shift type per day
 */
function validateStaffingRequirements(
  nurses: NurseWithLevel[],
  schedule: ScheduleData,
  year: number,
  month: number,
  days: number,
  wardConfigs: WardConfig[],
  violations: Violation[]
) {
  for (let d = 1; d <= days; d++) {
    const key = dateKey(year, month, d);
    for (const config of wardConfigs) {
      const shiftType = config.shift_type as ShiftType;
      if (shiftType === "X") continue;

      const assignedNurses = nurses.filter(
        (n) => (schedule[n.id]?.[key] ?? "X") === shiftType
      );

      if (assignedNurses.length < config.required_nurses) {
        const shiftName = shiftType === "D" ? "Day" : shiftType === "E" ? "Evening" : "Night";
        const shortage = config.required_nurses - assignedNurses.length;
        violations.push({
          nurseId: "__staffing__",
          date: key,
          rule: "understaffed",
          severity: "warning",
          message: `${shiftName} shift on day ${d} is short ${shortage} nurse(s) — has ${assignedNurses.length} of ${config.required_nurses} required. Fix: assign ${shortage} more nurse(s) to the ${shiftType} shift on this day.`,
        });
      }
    }
  }
}

/**
 * Exclusion pairs should not work the same shift on the same day
 */
function validateExclusions(
  nurses: NurseWithLevel[],
  schedule: ScheduleData,
  year: number,
  month: number,
  days: number,
  exclusions: { nurse_id_1: string; nurse_id_2: string }[],
  violations: Violation[]
) {
  for (let d = 1; d <= days; d++) {
    const key = dateKey(year, month, d);
    for (const excl of exclusions) {
      const s1 = schedule[excl.nurse_id_1]?.[key] ?? "X";
      const s2 = schedule[excl.nurse_id_2]?.[key] ?? "X";
      if (s1 !== "X" && s1 === s2) {
        const n1 = nurses.find((n) => n.id === excl.nurse_id_1);
        const n2 = nurses.find((n) => n.id === excl.nurse_id_2);
        violations.push({
          nurseId: excl.nurse_id_1,
          date: key,
          rule: "exclusion",
          severity: "error",
          message: `${n1?.name ?? "?"} and ${n2?.name ?? "?"} are both on the ${s1} shift on day ${d}. These nurses should not work the same shift. Fix: move one of them to a different shift or day.`,
        });
      }
    }
  }
}

/**
 * Build a lookup of violations by nurseId+date for grid display
 */
export function buildViolationMap(violations: Violation[]): Record<string, Violation[]> {
  const map: Record<string, Violation[]> = {};
  for (const v of violations) {
    const key = `${v.nurseId}:${v.date}`;
    if (!map[key]) map[key] = [];
    map[key].push(v);
  }
  return map;
}

/**
 * Calculate schedule score
 */
export function scoreSchedule(
  nurses: NurseWithLevel[],
  schedule: ScheduleData,
  year: number,
  month: number,
  wardConfigs: WardConfig[],
  exclusions: { nurse_id_1: string; nurse_id_2: string }[] = []
): { cost: number; fairness: number; preference: number; violations: number; total: number } {
  const violations = validateSchedule(nurses, schedule, year, month, wardConfigs, exclusions);
  const days = getDaysInMonth(year, month);

  // Cost calculation (lower is better)
  let totalCost = 0;
  const BASE_RATE = 30;
  const NIGHT_DIFF = 10;
  const OVERTIME_RATE = 45;

  for (const nurse of nurses) {
    let monthShifts = 0;
    let weekShifts = 0;
    for (let d = 1; d <= days; d++) {
      const key = dateKey(year, month, d);
      const shift = schedule[nurse.id]?.[key] ?? "X";
      if (shift !== "X") {
        monthShifts++;
        weekShifts++;
        const hours = 8;
        if (shift === "N") {
          totalCost += (BASE_RATE + NIGHT_DIFF) * hours;
        } else if (weekShifts > 5) {
          totalCost += OVERTIME_RATE * hours;
        } else {
          totalCost += BASE_RATE * hours;
        }
      }
      const date = new Date(year, month, d);
      if (date.getDay() === 0) weekShifts = 0;
    }
  }

  // Fairness (standard deviation of total shifts per nurse, lower is better)
  const shiftCounts = nurses.map((n) => {
    let count = 0;
    for (let d = 1; d <= days; d++) {
      const key = dateKey(year, month, d);
      if ((schedule[n.id]?.[key] ?? "X") !== "X") count++;
    }
    return count;
  });
  const avgShifts = shiftCounts.reduce((a, b) => a + b, 0) / (shiftCounts.length || 1);
  const variance = shiftCounts.reduce((sum, c) => sum + (c - avgShifts) ** 2, 0) / (shiftCounts.length || 1);
  const fairnessScore = Math.round(Math.max(0, 100 - Math.sqrt(variance) * 20));

  const errorCount = violations.filter((v) => v.severity === "error").length;
  const warnCount = violations.filter((v) => v.severity === "warning").length;
  const violationScore = Math.max(0, 100 - errorCount * 15 - warnCount * 5);

  const costScore = Math.round(Math.max(0, 100 - (totalCost / (nurses.length || 1) / 5000) * 100));

  const total = Math.round((costScore * 0.25 + fairnessScore * 0.35 + violationScore * 0.4));

  return {
    cost: costScore,
    fairness: fairnessScore,
    preference: 50, // placeholder - would need preference data
    violations: violationScore,
    total,
  };
}
