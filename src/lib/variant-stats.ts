import { dateKey, getDaysInMonth } from "./scheduler-data";
import type { ScheduleData } from "./scheduler-data";
import { validateSchedule, estimateCost } from "./schedule-constraints";
import type { NurseWithLevel, WardConfig, Violation } from "./schedule-constraints";

export interface TempSummary {
  id: string;
  name: string;
  level: number;
  shift_count: number;
  dates: string[];
}

export interface VariantStats {
  /** Temps the variant was allowed, and how many it actually used. */
  tempsAllowed: number;
  tempsUsed: number;
  /** Shifts bought from temps, and the dates - in effect the hiring spec. */
  tempShifts: number;
  errors: number;
  warnings: number;
  /** Understaffed shift-days still open. */
  coverageGaps: number;
  /** Overtime warnings that land on permanent staff, not temps. */
  permanentOvertime: number;
  /** Estimated payroll, and the delta against the baseline schedule. */
  cost: number;
  costDelta: number | null;
  /** Of the requests assumed approved, how many got every day off. */
  requestsHonored: number;
  requestsConsidered: number;
}

export interface AssumedRequest {
  nurse_id: string;
  start_date: string;
  end_date: string;
}

/**
 * The figures a manager needs to choose between temp-nurse alternatives.
 *
 * Generating several options moves the manager from writing schedules to judging
 * them, and judging needs numbers that map onto real decisions: how many temps,
 * for which days, at what extra cost, and whose time off it protects.
 */
export function summarizeVariant(params: {
  nurses: NurseWithLevel[];
  schedule: ScheduleData;
  year: number;
  month: number;
  wardConfigs: WardConfig[];
  exclusions: { nurse_id_1: string; nurse_id_2: string }[];
  temps: TempSummary[];
  tempsAllowed: number;
  baselineCost?: number | null;
  assumedRequests?: AssumedRequest[];
}): VariantStats {
  const {
    nurses, schedule, year, month, wardConfigs, exclusions,
    temps, tempsAllowed, baselineCost, assumedRequests = [],
  } = params;

  // The temps must be in the nurses array for this to be right: leave them out
  // and the coverage check counts only permanent staff, so the very variant that
  // closes a gap gets reported as still understaffed.
  const violations: Violation[] = validateSchedule(
    nurses, schedule, year, month, wardConfigs, exclusions
  );
  // Any temp, not just the invented ones: a temp already on the books is not
  // permanent staff either, and this column is about the regular team's load.
  const tempIds = new Set<string>([
    ...temps.map((t) => t.id),
    ...nurses.filter((n) => n.badge === "temp" || n.badge === "phantom").map((n) => n.id),
  ]);

  const cost = estimateCost(nurses, schedule, year, month);

  let honored = 0;
  for (const r of assumedRequests) {
    const dates = isoRange(r.start_date, r.end_date).filter(
      (d) => d >= monthStart(year, month) && d <= monthEnd(year, month)
    );
    if (dates.length === 0) continue;
    if (dates.every((d) => (schedule[r.nurse_id]?.[d] ?? "X") === "X")) honored++;
  }
  const considered = assumedRequests.filter((r) => {
    const dates = isoRange(r.start_date, r.end_date);
    return dates.some((d) => d >= monthStart(year, month) && d <= monthEnd(year, month));
  }).length;

  return {
    tempsAllowed,
    tempsUsed: temps.length,
    tempShifts: temps.reduce((sum, t) => sum + t.shift_count, 0),
    errors: violations.filter((v) => v.severity === "error").length,
    warnings: violations.filter((v) => v.severity === "warning").length,
    coverageGaps: violations.filter((v) => v.rule === "understaffed").length,
    permanentOvertime: violations.filter(
      (v) => v.rule === "overtime" && !tempIds.has(v.nurseId)
    ).length,
    cost,
    costDelta: baselineCost == null ? null : cost - baselineCost,
    requestsHonored: honored,
    requestsConsidered: considered,
  };
}

/** Every day in the month a nurse is scheduled off, for spot checks. */
export function offDays(
  schedule: ScheduleData,
  nurseId: string,
  year: number,
  month: number
): string[] {
  const out: string[] = [];
  for (let d = 1; d <= getDaysInMonth(year, month); d++) {
    const key = dateKey(year, month, d);
    if ((schedule[nurseId]?.[key] ?? "X") === "X") out.push(key);
  }
  return out;
}

function monthStart(year: number, month: number): string {
  return dateKey(year, month, 1);
}

function monthEnd(year: number, month: number): string {
  return dateKey(year, month, getDaysInMonth(year, month));
}

/** Inclusive ISO range in UTC, so a range never slides by a day. */
function isoRange(start: string, end: string): string[] {
  const out: string[] = [];
  const a = /^(\d{4})-(\d{2})-(\d{2})/.exec(start);
  const b = /^(\d{4})-(\d{2})-(\d{2})/.exec(end);
  if (!a || !b) return out;
  const d = new Date(Date.UTC(+a[1], +a[2] - 1, +a[3]));
  const stop = new Date(Date.UTC(+b[1], +b[2] - 1, +b[3]));
  while (d.getTime() <= stop.getTime() && out.length < 400) {
    out.push(d.toISOString().slice(0, 10));
    d.setUTCDate(d.getUTCDate() + 1);
  }
  return out;
}
