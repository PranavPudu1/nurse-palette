import { describe, it, expect } from "vitest";
import { summarizeVariant } from "@/lib/variant-stats";
import { estimateCost } from "@/lib/schedule-constraints";
import type { NurseWithLevel, WardConfig } from "@/lib/schedule-constraints";
import type { ScheduleData } from "@/lib/scheduler-data";

const year = 2026;
const month = 9; // October, 31 days
const configs: WardConfig[] = [
  { shift_type: "D", required_nurses: 1, level_mix: {} },
];

/** A month where `workDays` are day shifts and the rest are off. */
function schedule(nurseId: string, workDays: number[]): ScheduleData {
  const out: Record<string, any> = {};
  for (let d = 1; d <= 31; d++) {
    out[`2026-10-${String(d).padStart(2, "0")}`] = workDays.includes(d) ? "D" : "X";
  }
  return { [nurseId]: out };
}

describe("summarizeVariant", () => {
  const perm: NurseWithLevel[] = [{ id: "p1", name: "P1", level: 2 }];

  it("counts the temps used, not the temps allowed", () => {
    const nurses: NurseWithLevel[] = [...perm, { id: "__temp_1_1__", name: "Temp", level: 2 }];
    const stats = summarizeVariant({
      nurses,
      schedule: { ...schedule("p1", [1, 2]), ...schedule("__temp_1_1__", [3, 4]) },
      year, month, wardConfigs: configs, exclusions: [],
      temps: [{ id: "__temp_1_1__", name: "Temp", level: 2, shift_count: 2, dates: ["2026-10-03", "2026-10-04"] }],
      tempsAllowed: 3,
    });
    expect(stats.tempsAllowed).toBe(3);
    expect(stats.tempsUsed).toBe(1);
    expect(stats.tempShifts).toBe(2);
  });

  it("does not report a gap the temp closed", () => {
    // The whole month is covered, but only because the temp takes half of it.
    // Leaving the temp out of the nurses array would make this look understaffed.
    const tempDays = Array.from({ length: 31 }, (_, i) => i + 1).filter((d) => d % 2 === 0);
    const permDays = Array.from({ length: 31 }, (_, i) => i + 1).filter((d) => d % 2 === 1);
    const nurses: NurseWithLevel[] = [...perm, { id: "t", name: "Temp", level: 2 }];
    const full = { ...schedule("p1", permDays), ...schedule("t", tempDays) };

    const withTemp = summarizeVariant({
      nurses, schedule: full, year, month, wardConfigs: configs, exclusions: [],
      temps: [{ id: "t", name: "Temp", level: 2, shift_count: tempDays.length, dates: [] }],
      tempsAllowed: 1,
    });
    const withoutTemp = summarizeVariant({
      nurses: perm, schedule: full, year, month, wardConfigs: configs, exclusions: [],
      temps: [], tempsAllowed: 1,
    });

    expect(withTemp.coverageGaps).toBe(0);
    expect(withoutTemp.coverageGaps).toBeGreaterThan(0);
  });

  it("attributes overtime to permanent staff only", () => {
    // Both work every day, so both are over the weekly limit; only the
    // permanent nurse's overtime is the manager's problem.
    const every = Array.from({ length: 31 }, (_, i) => i + 1);
    const nurses: NurseWithLevel[] = [...perm, { id: "t", name: "Temp", level: 2 }];
    const stats = summarizeVariant({
      nurses,
      schedule: { ...schedule("p1", every), ...schedule("t", every) },
      year, month, wardConfigs: configs, exclusions: [],
      temps: [{ id: "t", name: "Temp", level: 2, shift_count: 31, dates: [] }],
      tempsAllowed: 1,
    });
    expect(stats.permanentOvertime).toBeGreaterThan(0);
    const all = stats.warnings;
    expect(stats.permanentOvertime).toBeLessThan(all);
  });

  it("reports cost as a delta against the baseline", () => {
    const sched = schedule("p1", [1, 2, 3]);
    const baseline = estimateCost(perm, schedule("p1", [1]), year, month);
    const stats = summarizeVariant({
      nurses: perm, schedule: sched, year, month, wardConfigs: configs,
      exclusions: [], temps: [], tempsAllowed: 0, baselineCost: baseline,
    });
    expect(stats.cost).toBe(estimateCost(perm, sched, year, month));
    expect(stats.costDelta).toBe(stats.cost - baseline);
  });

  it("leaves the delta empty when there is no baseline to compare with", () => {
    const stats = summarizeVariant({
      nurses: perm, schedule: schedule("p1", [1]), year, month,
      wardConfigs: configs, exclusions: [], temps: [], tempsAllowed: 0,
    });
    expect(stats.costDelta).toBeNull();
  });

  it("counts a time-off request as honored only when every day is free", () => {
    const requests = [
      { nurse_id: "p1", start_date: "2026-10-10", end_date: "2026-10-12" },
      { nurse_id: "p1", start_date: "2026-10-20", end_date: "2026-10-21" },
    ];
    // Day 11 is worked, so the first request is broken; the second is clear.
    const stats = summarizeVariant({
      nurses: perm, schedule: schedule("p1", [11]), year, month,
      wardConfigs: configs, exclusions: [], temps: [], tempsAllowed: 0,
      assumedRequests: requests,
    });
    expect(stats.requestsConsidered).toBe(2);
    expect(stats.requestsHonored).toBe(1);
  });

  it("ignores a request that falls outside the displayed month", () => {
    const stats = summarizeVariant({
      nurses: perm, schedule: schedule("p1", []), year, month,
      wardConfigs: configs, exclusions: [], temps: [], tempsAllowed: 0,
      assumedRequests: [{ nurse_id: "p1", start_date: "2026-12-01", end_date: "2026-12-02" }],
    });
    expect(stats.requestsConsidered).toBe(0);
    expect(stats.requestsHonored).toBe(0);
  });
});

describe("scoreSchedule fairness exclusion", () => {
  it("does not let a temp's short stint read as unfairness", async () => {
    const { scoreSchedule } = await import("@/lib/schedule-constraints");
    const perm: NurseWithLevel[] = [
      { id: "p1", name: "P1", level: 2 },
      { id: "p2", name: "P2", level: 2 },
    ];
    const withTemp: NurseWithLevel[] = [...perm, { id: "t", name: "Temp", level: 2 }];
    const twenty = Array.from({ length: 20 }, (_, i) => i + 1);
    const sched = {
      ...schedule("p1", twenty),
      ...schedule("p2", twenty),
      ...schedule("t", [1, 2]),
    };

    const naive = scoreSchedule(withTemp, sched, year, month, configs, []);
    const excluded = scoreSchedule(withTemp, sched, year, month, configs, [], {
      fairnessExclude: new Set(["t"]),
    });

    // The permanent staff are perfectly even; only the temp's 2 shifts against
    // their 20 creates spread, and that is a hiring fact, not an unfair roster.
    expect(naive.fairness).toBeLessThan(excluded.fairness);
    expect(excluded.fairness).toBe(100);
  });

  it("is unchanged when nothing is excluded", async () => {
    const { scoreSchedule } = await import("@/lib/schedule-constraints");
    const perm: NurseWithLevel[] = [{ id: "p1", name: "P1", level: 2 }];
    const sched = schedule("p1", [1, 2, 3]);
    const a = scoreSchedule(perm, sched, year, month, configs, []);
    const b = scoreSchedule(perm, sched, year, month, configs, [], { fairnessExclude: new Set() });
    expect(a).toEqual(b);
  });
});
