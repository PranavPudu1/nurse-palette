import { useState, useMemo } from "react";
import { Trash2, Plus } from "lucide-react";
import { Nurse, ScheduleData, getDaysInMonth, dateKey, ShiftType } from "@/lib/scheduler-data";
import { ShiftCell } from "@/components/ShiftCell";
import { ViolationIndicator } from "@/components/ViolationIndicator";
import type { Violation } from "@/lib/schedule-constraints";
import { buildViolationMap } from "@/lib/schedule-constraints";

interface ScheduleGridProps {
  nurses: Nurse[];
  schedule: ScheduleData;
  year: number;
  month: number;
  readOnly?: boolean;
  violations?: Violation[];
  onCellClick?: (nurseId: string, key: string) => void;
  onCellClear?: (nurseId: string, key: string) => void;
  onRemoveNurse?: (nurseId: string) => void;
  onAddNurse?: (name: string) => void;
  onNurseNameClick?: (nurseId: string) => void;
}

const DAY_ABBR = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

export function ScheduleGrid({
  nurses,
  schedule,
  year,
  month,
  readOnly = false,
  violations = [],
  onCellClick,
  onCellClear,
  onRemoveNurse,
  onAddNurse,
  onNurseNameClick,
}: ScheduleGridProps) {
  const days = getDaysInMonth(year, month);
  const [newName, setNewName] = useState("");
  const violationMap = useMemo(() => buildViolationMap(violations), [violations]);

  const handleAdd = () => {
    const trimmed = newName.trim();
    if (trimmed && onAddNurse) {
      onAddNurse(trimmed);
      setNewName("");
    }
  };

  // Staffing violations (not tied to a specific nurse)
  const staffingViolations = useMemo(() =>
    violations.filter((v) => v.nurseId === "__staffing__"),
    [violations]
  );

  return (
    <div className="flex flex-col gap-3">
      <div className="overflow-auto rounded-lg border border-grid-border bg-card shadow-sm">
        <table className="border-collapse" style={{ overflow: "visible" }}>
          <thead>
            <tr>
              <th className="sticky left-0 z-20 bg-grid-header px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider min-w-[160px] border-b border-r border-grid-border">
                Nurse
              </th>
              {Array.from({ length: days }, (_, i) => {
                const d = i + 1;
                const dow = new Date(year, month, d).getDay();
                const isWeekend = dow === 0 || dow === 6;
                const key = dateKey(year, month, d);
                const dayStaffingIssues = staffingViolations.filter((v) => v.date === key);
                return (
                  <th
                    key={d}
                    className={`sticky top-0 z-10 px-1 py-1.5 text-center text-[10px] font-medium border-b border-grid-border min-w-[40px] relative ${
                      isWeekend ? "bg-accent/60 text-accent-foreground" : "bg-grid-header text-muted-foreground"
                    } ${dayStaffingIssues.length > 0 ? "bg-amber-50" : ""}`}
                  >
                    <div>{DAY_ABBR[dow]}</div>
                    <div className="text-xs font-semibold text-foreground">{d}</div>
                    {dayStaffingIssues.length > 0 && (
                      <ViolationIndicator violations={dayStaffingIssues} />
                    )}
                  </th>
                );
              })}
              {!readOnly && (
                <th className="sticky top-0 z-10 bg-grid-header border-b border-grid-border w-10" />
              )}
            </tr>
          </thead>
          <tbody>
            {nurses.map((nurse) => (
              <tr key={nurse.id} className="group hover:bg-grid-hover/40">
                <td className="sticky left-0 z-10 bg-card group-hover:bg-grid-hover/60 px-4 py-1.5 text-sm font-medium border-b border-r border-grid-border whitespace-nowrap">
                  <button
                    onClick={() => onNurseNameClick?.(nurse.id)}
                    className="text-left hover:text-primary hover:underline transition-colors cursor-pointer"
                  >
                    {nurse.name}
                  </button>
                </td>
                {Array.from({ length: days }, (_, i) => {
                  const key = dateKey(year, month, i + 1);
                  const val: ShiftType = schedule[nurse.id]?.[key] ?? "X";
                  const cellViolations = violationMap[`${nurse.id}:${key}`] ?? [];
                  return (
                    <td key={key} className="px-0.5 py-0.5 border-b border-grid-border text-center relative">
                      <ShiftCell
                        value={val}
                        readOnly={readOnly}
                        onClick={() => onCellClick?.(nurse.id, key)}
                        onContextMenu={(e) => {
                          e.preventDefault();
                          onCellClear?.(nurse.id, key);
                        }}
                      />
                      <ViolationIndicator violations={cellViolations} />
                    </td>
                  );
                })}
                {!readOnly && (
                  <td className="border-b border-grid-border px-1">
                    <button
                      onClick={() => onRemoveNurse?.(nurse.id)}
                      className="p-1.5 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors opacity-0 group-hover:opacity-100"
                      aria-label={`Remove ${nurse.name}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {!readOnly && onAddNurse && (
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
            placeholder="New nurse name…"
            className="px-3 py-2 text-sm rounded-md border border-input bg-card focus:outline-none focus:ring-2 focus:ring-ring/30 w-56"
          />
          <button
            onClick={handleAdd}
            disabled={!newName.trim()}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-40 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Nurse
          </button>
        </div>
      )}
    </div>
  );
}
