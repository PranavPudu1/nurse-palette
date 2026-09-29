import { useState, useMemo } from "react";
import type { ScheduleData, Nurse, ShiftType } from "@/lib/scheduler-data";
import type { NurseWithLevel, WardConfig } from "@/lib/schedule-constraints";
import { scoreSchedule, validateSchedule } from "@/lib/schedule-constraints";
import { ScheduleGrid } from "./ScheduleGrid";
import { ViolationsPanel } from "./ViolationsPanel";
import { ViolationLegend } from "./ViolationLegend";
import { Legend } from "./Legend";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Check, AlertTriangle, DollarSign, Scale, Trophy, Info, UserPlus } from "lucide-react";
import { useLang } from "@/lib/i18n";
import { summarizeVariant } from "@/lib/variant-stats";
import type { TempSummary, AssumedRequest, VariantStats } from "@/lib/variant-stats";

interface ScheduleOption {
  id: string;
  label: string;
  schedule: ScheduleData;
  /** Temps this specific option hires. Two options for the same budget can
   *  hire different people, so it is per option rather than per variant. */
  temps?: TempSummary[];
}

/** One temp-count alternative, as returned by the optimizer. */
export interface TempVariant {
  temp_count: number;
  status: "feasible" | "infeasible" | "no_solution_found";
  options: ScheduleOption[];
  temps: TempSummary[];
}

interface Props {
  options: ScheduleOption[];
  nurses: NurseWithLevel[];
  year: number;
  month: number;
  wardConfigs: WardConfig[];
  exclusions: { nurse_id_1: string; nurse_id_2: string }[];
  onApply: (schedule: ScheduleData, temps?: TempSummary[]) => void;
  onClose: () => void;
  /** Present when comparing "what if we hire temps" alternatives. */
  variants?: TempVariant[];
  minFeasibleCount?: number | null;
  /** Requests the generation assumed approved, so we can report which held up. */
  assumedRequests?: AssumedRequest[];
  /** Payroll for the schedule without temps, for the cost delta. */
  baselineCost?: number | null;
}

function ScoreBar({ label, value, icon, help }: { label: string; value: number; icon: React.ReactNode; help?: string }) {
  const color = value >= 70 ? "bg-emerald-500" : value >= 40 ? "bg-amber-500" : "bg-destructive";
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        {icon}
        {label}
        {help && (
          <Tooltip delayDuration={100}>
            <TooltipTrigger asChild>
              <span className="cursor-help" onClick={(e) => e.stopPropagation()}>
                <Info className="w-3 h-3 text-muted-foreground/70" />
              </span>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-[240px] z-50 text-xs">
              {help}
            </TooltipContent>
          </Tooltip>
        )}
        <span className="ml-auto font-semibold text-foreground">{value}</span>
      </div>
      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

export function ScheduleComparison({
  options,
  nurses,
  year,
  month,
  wardConfigs,
  exclusions,
  onApply,
  onClose,
  variants,
  minFeasibleCount,
  assumedRequests = [],
  baselineCost = null,
}: Props) {
  const { t } = useLang();
  const [selectedIdx, setSelectedIdx] = useState(0);

  // ── Temp variants ──────────────────────────────────────────────────────────
  const feasibleVariants = useMemo(
    () => (variants ?? []).filter((v) => v.status === "feasible" && v.options.length > 0),
    [variants]
  );
  const unreachable = useMemo(
    () => (variants ?? []).filter((v) => v.status !== "feasible"),
    [variants]
  );
  const [variantIdx, setVariantIdx] = useState(0);
  const activeVariant = feasibleVariants[variantIdx];

  const shownOptions = activeVariant ? activeVariant.options : options;
  // Switching temp count can shrink the option list under the current
  // selection, so every read goes through the clamped index.
  const safeIdx = Math.min(selectedIdx, Math.max(0, shownOptions.length - 1));

  // The phantom temps have to join the nurse list before anything is measured.
  // Left out, the coverage check ignores their shifts and reports the schedule
  // that fixes a gap as still short-staffed.
  const activeTemps: TempSummary[] = shownOptions[safeIdx]?.temps ?? [];
  const nursesForScoring: NurseWithLevel[] = useMemo(
    () => activeTemps.length
      ? [
          ...nurses,
          ...activeTemps.map((tp) => ({
            id: tp.id,
            name: tp.name,
            level: tp.level,
            badge: "phantom" as const,
          })),
        ]
      : nurses,
    [nurses, activeTemps]
  );
  const tempIdSet = useMemo(() => new Set(activeTemps.map((tp) => tp.id)), [activeTemps]);

  const scores = useMemo(
    () => shownOptions.map((opt) => scoreSchedule(
      nursesForScoring, opt.schedule, year, month, wardConfigs, exclusions,
      { fairnessExclude: tempIdSet }
    )),
    [shownOptions, nursesForScoring, year, month, wardConfigs, exclusions, tempIdSet]
  );

  // One row per temp count, which is what answers "which alternative", as
  // opposed to the bars, which answer "how good is this one".
  const variantStats = useMemo<{ variant: TempVariant; stats: VariantStats }[]>(
    () => feasibleVariants.map((v) => {
      const rowTemps = v.options[0].temps ?? [];
      const withTemps: NurseWithLevel[] = [
        ...nurses,
        ...rowTemps.map((tp) => ({
          id: tp.id, name: tp.name, level: tp.level, badge: "phantom" as const,
        })),
      ];
      return {
        variant: v,
        stats: summarizeVariant({
          nurses: withTemps,
          schedule: v.options[0].schedule,
          year,
          month,
          wardConfigs,
          exclusions,
          temps: rowTemps,
          tempsAllowed: v.temp_count,
          baselineCost,
          assumedRequests,
        }),
      };
    }),
    [feasibleVariants, nurses, year, month, wardConfigs, exclusions, baselineCost, assumedRequests]
  );

  const violationsByOption = useMemo(
    () => shownOptions.map((opt) =>
      validateSchedule(nursesForScoring, opt.schedule, year, month, wardConfigs, exclusions)),
    [shownOptions, nursesForScoring, year, month, wardConfigs, exclusions]
  );

  const violationCounts = useMemo(
    () => violationsByOption.map((v) => ({
      errors: v.filter((x) => x.severity === "error").length,
      warnings: v.filter((x) => x.severity === "warning").length,
    })),
    [violationsByOption]
  );

  const nurseNames = useMemo(
    () => Object.fromEntries(nursesForScoring.map((n) => [n.id, n.name])),
    [nursesForScoring]
  );

  const bestIdx = scores.reduce((best, s, i) => (s.total > scores[best].total ? i : best), 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{t("cmp.title")}</h2>
        <button
          onClick={onClose}
          className="px-3 py-1.5 text-sm rounded-md bg-secondary text-secondary-foreground hover:bg-accent transition-colors"
        >
          {t("cmp.cancel")}
        </button>
      </div>

      {/* Counts that cannot work at all: stated once, not as three empty cards. */}
      {unreachable.length > 0 && (
        <div className="rounded-md border border-destructive/40 bg-destructive/5 px-3 py-2 text-sm text-destructive">
          {unreachable.map((v) => (
            <div key={v.temp_count}>
              {v.status === "infeasible"
                ? t("temp.notEnough", { n: v.temp_count })
                : t("temp.timedOut", { n: v.temp_count })}
            </div>
          ))}
          {feasibleVariants.length === 0 && (
            <p className="mt-1 text-xs">{t("temp.noneWork")}</p>
          )}
        </div>
      )}

      {/* Which alternative, rather than how good one is. Generating options moves
          the manager from writing schedules to judging them, and judging needs
          figures that map onto real decisions. */}
      {variantStats.length > 0 && (
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <UserPlus className="w-4 h-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold">{t("temp.tableTitle")}</h3>
            {minFeasibleCount != null && (
              <span className="text-xs text-muted-foreground">
                {t("temp.minFeasible", { n: minFeasibleCount })}
              </span>
            )}
          </div>
          <div className="overflow-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead className="bg-muted/60 text-xs text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 text-left font-medium">{t("temp.colTemps")}</th>
                  <th className="px-3 py-2 text-left font-medium">{t("temp.colShifts")}</th>
                  <th className="px-3 py-2 text-left font-medium">{t("temp.colCost")}</th>
                  <th className="px-3 py-2 text-left font-medium">{t("temp.colErrors")}</th>
                  <th className="px-3 py-2 text-left font-medium">{t("temp.colGaps")}</th>
                  <th className="px-3 py-2 text-left font-medium">{t("temp.colOvertime")}</th>
                  <th className="px-3 py-2 text-left font-medium">{t("temp.colRequests")}</th>
                  <th className="px-3 py-2 text-left font-medium">{t("temp.colDates")}</th>
                </tr>
              </thead>
              <tbody>
                {variantStats.map(({ variant, stats }, idx) => (
                  <tr
                    key={variant.temp_count}
                    onClick={() => { setVariantIdx(idx); setSelectedIdx(0); }}
                    className={`cursor-pointer border-t border-border transition-colors ${
                      idx === variantIdx ? "bg-primary/5" : "hover:bg-muted/40"
                    }`}
                  >
                    <td className="px-3 py-2 font-medium">
                      {stats.tempsUsed === stats.tempsAllowed
                        ? t("temp.usedN", { n: stats.tempsUsed })
                        : t("temp.usedOfAllowed", { used: stats.tempsUsed, allowed: stats.tempsAllowed })}
                    </td>
                    <td className="px-3 py-2">{stats.tempShifts}</td>
                    <td className="px-3 py-2">
                      {stats.cost.toLocaleString()}
                      {stats.costDelta != null && (
                        <span className={stats.costDelta > 0 ? "text-destructive ml-1" : "text-emerald-600 ml-1"}>
                          ({stats.costDelta > 0 ? "+" : ""}{stats.costDelta.toLocaleString()})
                        </span>
                      )}
                    </td>
                    <td className={`px-3 py-2 ${stats.errors > 0 ? "text-destructive font-semibold" : ""}`}>
                      {stats.errors}
                    </td>
                    <td className="px-3 py-2">{stats.coverageGaps}</td>
                    <td className="px-3 py-2">{stats.permanentOvertime}</td>
                    <td className="px-3 py-2">
                      {stats.requestsConsidered > 0
                        ? `${stats.requestsHonored}/${stats.requestsConsidered}`
                        : "—"}
                    </td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">
                      {(variant.options[0].temps ?? []).map((tp) =>
                        `L${tp.level}: ${tp.dates.map((d) => d.slice(8)).join(", ")}`
                      ).join(" · ") || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-muted-foreground">{t("temp.datesAreSpec")}</p>
        </div>
      )}

      {/* Score cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {shownOptions.map((opt, idx) => (
          <button
            key={opt.id}
            onClick={() => setSelectedIdx(idx)}
            className={`relative rounded-lg border p-4 text-left transition-all ${
              safeIdx === idx
                ? "border-primary ring-2 ring-primary/20 bg-card"
                : "border-border bg-card hover:border-primary/40"
            }`}
          >
            {idx === bestIdx && (
              <span className="absolute -top-2 -right-2 bg-primary text-primary-foreground text-[10px] font-bold px-1.5 py-0.5 rounded-full flex items-center gap-0.5">
                <Trophy className="w-3 h-3" /> {t("cmp.best")}
              </span>
            )}
            <div className="text-sm font-semibold mb-3">{opt.label}</div>
            <div className="space-y-2.5">
              <ScoreBar label={t("cmp.cost")} value={scores[idx].cost} icon={<DollarSign className="w-3 h-3" />}
                help={t("cmp.costHelp")} />
              <ScoreBar label={t("cmp.fairness")} value={scores[idx].fairness} icon={<Scale className="w-3 h-3" />}
                help={t("cmp.fairnessHelp")} />
              <ScoreBar label={t("cmp.violations")} value={scores[idx].violations} icon={<AlertTriangle className="w-3 h-3" />}
                help={t("cmp.violationsHelp")} />
            </div>
            <div className="mt-3 flex items-center gap-3 text-xs text-muted-foreground">
              <span className="text-destructive font-medium">{t("cmp.nErrorsHard", { n: violationCounts[idx].errors })}</span>
              <span className="text-amber-600 font-medium">{t("cmp.nWarningsSoft", { n: violationCounts[idx].warnings })}</span>
            </div>
            <div className="mt-2 flex items-center gap-1.5 text-lg font-bold text-foreground">
              {t("cmp.score", { n: scores[idx].total })}
              <Tooltip delayDuration={100}>
                <TooltipTrigger asChild>
                  <span className="cursor-help" onClick={(e) => e.stopPropagation()}>
                    <Info className="w-3.5 h-3.5 text-muted-foreground/70" />
                  </span>
                </TooltipTrigger>
                <TooltipContent side="top" className="max-w-[240px] z-50 text-xs font-normal">
                  {t("cmp.scoreHelp")}
                </TooltipContent>
              </Tooltip>
            </div>
          </button>
        ))}
      </div>

      {/* Selected schedule grid */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <h3 className="text-sm font-semibold">{t("cmp.preview", { label: shownOptions[safeIdx].label })}</h3>
          <Legend />
        </div>
        <ViolationLegend />
        <ScheduleGrid
          nurses={nursesForScoring}
          schedule={shownOptions[safeIdx].schedule}
          year={year}
          month={month}
          readOnly={true}
          violations={violationsByOption[safeIdx]}
        />
        <ViolationsPanel
          violations={violationsByOption[safeIdx]}
          nurseNames={nurseNames}
        />
      </div>

      {/* Apply button */}
      <div className="flex justify-end gap-3">
        <button
          onClick={() => onApply(shownOptions[safeIdx].schedule, activeTemps)}
          className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Check className="w-4 h-4" /> {t("cmp.apply", { label: shownOptions[safeIdx].label })}
        </button>
      </div>
    </div>
  );
}
