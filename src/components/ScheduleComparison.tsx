import { useState, useMemo } from "react";
import type { ScheduleData, Nurse, ShiftType } from "@/lib/scheduler-data";
import type { NurseWithLevel, WardConfig } from "@/lib/schedule-constraints";
import { scoreSchedule, validateSchedule } from "@/lib/schedule-constraints";
import { ScheduleGrid } from "./ScheduleGrid";
import { ViolationsPanel } from "./ViolationsPanel";
import { ViolationLegend } from "./ViolationLegend";
import { Legend } from "./Legend";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Check, AlertTriangle, DollarSign, Scale, Trophy, Info } from "lucide-react";
import { useLang } from "@/lib/i18n";

interface ScheduleOption {
  id: string;
  label: string;
  schedule: ScheduleData;
}

interface Props {
  options: ScheduleOption[];
  nurses: NurseWithLevel[];
  year: number;
  month: number;
  wardConfigs: WardConfig[];
  exclusions: { nurse_id_1: string; nurse_id_2: string }[];
  onApply: (schedule: ScheduleData) => void;
  onClose: () => void;
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

export function ScheduleComparison({ options, nurses, year, month, wardConfigs, exclusions, onApply, onClose }: Props) {
  const { t } = useLang();
  const [selectedIdx, setSelectedIdx] = useState(0);

  const gridNurses = useMemo(() => nurses.map((n) => ({ id: n.id, name: n.name })), [nurses]);

  const scores = useMemo(
    () => options.map((opt) => scoreSchedule(nurses, opt.schedule, year, month, wardConfigs, exclusions)),
    [options, nurses, year, month, wardConfigs, exclusions]
  );

  const violationsByOption = useMemo(
    () => options.map((opt) =>
      validateSchedule(nurses, opt.schedule, year, month, wardConfigs, exclusions)),
    [options, nurses, year, month, wardConfigs, exclusions]
  );

  const violationCounts = useMemo(
    () => violationsByOption.map((v) => ({
      errors: v.filter((x) => x.severity === "error").length,
      warnings: v.filter((x) => x.severity === "warning").length,
    })),
    [violationsByOption]
  );

  const nurseNames = useMemo(
    () => Object.fromEntries(nurses.map((n) => [n.id, n.name])),
    [nurses]
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

      {/* Score cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {options.map((opt, idx) => (
          <button
            key={opt.id}
            onClick={() => setSelectedIdx(idx)}
            className={`relative rounded-lg border p-4 text-left transition-all ${
              selectedIdx === idx
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
          <h3 className="text-sm font-semibold">{t("cmp.preview", { label: options[selectedIdx].label })}</h3>
          <Legend />
        </div>
        <ViolationLegend />
        <ScheduleGrid
          nurses={gridNurses}
          schedule={options[selectedIdx].schedule}
          year={year}
          month={month}
          readOnly={true}
          violations={violationsByOption[selectedIdx]}
        />
        <ViolationsPanel
          violations={violationsByOption[selectedIdx]}
          nurseNames={nurseNames}
        />
      </div>

      {/* Apply button */}
      <div className="flex justify-end gap-3">
        <button
          onClick={() => onApply(options[selectedIdx].schedule)}
          className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Check className="w-4 h-4" /> {t("cmp.apply", { label: options[selectedIdx].label })}
        </button>
      </div>
    </div>
  );
}
