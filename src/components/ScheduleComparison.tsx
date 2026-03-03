import { useState, useMemo } from "react";
import type { ScheduleData, Nurse, ShiftType } from "@/lib/scheduler-data";
import type { NurseWithLevel, WardConfig } from "@/lib/schedule-constraints";
import { scoreSchedule, validateSchedule } from "@/lib/schedule-constraints";
import { ScheduleGrid } from "./ScheduleGrid";
import { Legend } from "./Legend";
import { Check, AlertTriangle, DollarSign, Scale, Trophy } from "lucide-react";

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

function ScoreBar({ label, value, icon }: { label: string; value: number; icon: React.ReactNode }) {
  const color = value >= 70 ? "bg-emerald-500" : value >= 40 ? "bg-amber-500" : "bg-destructive";
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        {icon}
        {label}
        <span className="ml-auto font-semibold text-foreground">{value}</span>
      </div>
      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

export function ScheduleComparison({ options, nurses, year, month, wardConfigs, exclusions, onApply, onClose }: Props) {
  const [selectedIdx, setSelectedIdx] = useState(0);

  const gridNurses = useMemo(() => nurses.map((n) => ({ id: n.id, name: n.name })), [nurses]);

  const scores = useMemo(
    () => options.map((opt) => scoreSchedule(nurses, opt.schedule, year, month, wardConfigs, exclusions)),
    [options, nurses, year, month, wardConfigs, exclusions]
  );

  const violationCounts = useMemo(
    () => options.map((opt) => {
      const v = validateSchedule(nurses, opt.schedule, year, month, wardConfigs, exclusions);
      return { errors: v.filter((x) => x.severity === "error").length, warnings: v.filter((x) => x.severity === "warning").length };
    }),
    [options, nurses, year, month, wardConfigs, exclusions]
  );

  const bestIdx = scores.reduce((best, s, i) => (s.total > scores[best].total ? i : best), 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Compare Generated Schedules</h2>
        <button
          onClick={onClose}
          className="px-3 py-1.5 text-sm rounded-md bg-secondary text-secondary-foreground hover:bg-accent transition-colors"
        >
          Cancel
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
                <Trophy className="w-3 h-3" /> Best
              </span>
            )}
            <div className="text-sm font-semibold mb-3">{opt.label}</div>
            <div className="space-y-2.5">
              <ScoreBar label="Cost" value={scores[idx].cost} icon={<DollarSign className="w-3 h-3" />} />
              <ScoreBar label="Fairness" value={scores[idx].fairness} icon={<Scale className="w-3 h-3" />} />
              <ScoreBar label="Violations" value={scores[idx].violations} icon={<AlertTriangle className="w-3 h-3" />} />
            </div>
            <div className="mt-3 flex items-center gap-3 text-xs text-muted-foreground">
              <span className="text-destructive font-medium">{violationCounts[idx].errors} errors</span>
              <span className="text-amber-600 font-medium">{violationCounts[idx].warnings} warnings</span>
            </div>
            <div className="mt-2 text-lg font-bold text-foreground">
              Score: {scores[idx].total}
            </div>
          </button>
        ))}
      </div>

      {/* Selected schedule grid */}
      <div>
        <div className="flex items-center gap-3 mb-3">
          <h3 className="text-sm font-semibold">{options[selectedIdx].label} — Preview</h3>
          <Legend />
        </div>
        <ScheduleGrid
          nurses={gridNurses}
          schedule={options[selectedIdx].schedule}
          year={year}
          month={month}
          readOnly={true}
        />
      </div>

      {/* Apply button */}
      <div className="flex justify-end gap-3">
        <button
          onClick={() => onApply(options[selectedIdx].schedule)}
          className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Check className="w-4 h-4" /> Apply {options[selectedIdx].label}
        </button>
      </div>
    </div>
  );
}
