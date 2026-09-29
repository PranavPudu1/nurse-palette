import { useState, useMemo } from "react";
import { Trash2, Plus } from "lucide-react";
import { Nurse, ScheduleData, getDaysInMonth, dateKey, ShiftType } from "@/lib/scheduler-data";
import { ShiftCell } from "@/components/ShiftCell";
import { ViolationIndicator } from "@/components/ViolationIndicator";
import type { Violation } from "@/lib/schedule-constraints";
import { buildViolationMap } from "@/lib/schedule-constraints";
import { useLang, DAY_ABBR } from "@/lib/i18n";
import { NurseBadge } from "@/components/NurseBadge";
import type { TimeOffMap } from "@/lib/time-off";

interface ScheduleGridProps {
  nurses: Nurse[];
  schedule: ScheduleData;
  year: number;
  month: number;
  readOnly?: boolean;
  violations?: Violation[];
  /** Dotted line for a pending request, solid for an approved day off. */
  timeOff?: TimeOffMap;
  onCellClick?: (nurseId: string, key: string) => void;
  onCellClear?: (nurseId: string, key: string) => void;
  onRemoveNurse?: (nurseId: string) => void;
  onAddNurse?: (name: string) => void;
  onNurseNameClick?: (nurseId: string) => void;
}

/**
 * One segment of a time-off run, drawn on the cell rather than as a single
 * absolutely-positioned span across N columns: the day columns are min-width,
 * so a measured span drifts. The table already collapses borders, so adjacent
 * segments join into one continuous line.
 *
 * pointer-events-none matters - without it this would swallow the click that
 * cycles the shift.
 */
function TimeOffRun({ marker }: { marker: { status: string; isStart: boolean; isEnd: boolean } }) {
  const line = marker.status === "approved" ? "border-solid" : "border-dashed";
  const hue = marker.status === "approved"
    ? "border-shift-timeoff-foreground"
    : "border-shift-timeoff-foreground/60";
  return (
    <span
      aria-hidden
      className={[
        "pointer-events-none absolute inset-x-0 top-0 bottom-0 z-20 border-y-2",
        line,
        hue,
        marker.isStart ? `border-l-2 ${line} rounded-l-sm` : "",
        marker.isEnd ? `border-r-2 ${line} rounded-r-sm` : "",
      ].join(" ")}
    />
  );
}

export function ScheduleGrid({
  nurses,
  schedule,
  year,
  month,
  readOnly = false,
  violations = [],
  timeOff = {},
  onCellClick,
  onCellClear,
  onRemoveNurse,
  onAddNurse,
  onNurseNameClick,
}: ScheduleGridProps) {
  const { lang, t } = useLang();
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
                {t("grid.nurse")}
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
                    <div>{DAY_ABBR[lang][dow]}</div>
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
                  <span className="inline-flex items-center gap-1.5">
                    <button
                      onClick={() => onNurseNameClick?.(nurse.id)}
                      className="text-left hover:text-primary hover:underline transition-colors cursor-pointer"
                    >
                      {nurse.name}
                    </button>
                    <NurseBadge kind={nurse.badge} />
                  </span>
                </td>
                {Array.from({ length: days }, (_, i) => {
                  const day = i + 1;
                  const key = dateKey(year, month, day);
                  const val: ShiftType = schedule[nurse.id]?.[key] ?? "X";
                  const cellViolations = violationMap[`${nurse.id}:${key}`] ?? [];
                  const off = timeOff[`${nurse.id}:${key}`];
                  const outside =
                    (nurse.availableFrom !== undefined && day < nurse.availableFrom) ||
                    (nurse.availableUntil !== undefined && day > nurse.availableUntil);
                  return (
                    <td key={key} className="px-0.5 py-0.5 border-b border-grid-border text-center relative">
                      <ShiftCell
                        value={val}
                        readOnly={readOnly}
                        timeOff={off?.status}
                        outsideWindow={outside}
                        label={off ? `${t(`shift.O.${off.status}`)}: ${key}` : undefined}
                        onClick={() => onCellClick?.(nurse.id, key)}
                        onContextMenu={(e) => {
                          e.preventDefault();
                          onCellClear?.(nurse.id, key);
                        }}
                      />
                      {off && <TimeOffRun marker={off} />}
                      <ViolationIndicator violations={cellViolations} />
                    </td>
                  );
                })}
                {!readOnly && (
                  <td className="border-b border-grid-border px-1">
                    <button
                      onClick={() => onRemoveNurse?.(nurse.id)}
                      className="p-1.5 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors opacity-0 group-hover:opacity-100"
                      aria-label={t("grid.remove", { name: nurse.name })}
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
            placeholder={t("grid.newNurse")}
            className="px-3 py-2 text-sm rounded-md border border-input bg-card focus:outline-none focus:ring-2 focus:ring-ring/30 w-56"
          />
          <button
            onClick={handleAdd}
            disabled={!newName.trim()}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-40 transition-colors"
          >
            <Plus className="w-4 h-4" />
            {t("grid.addNurse")}
          </button>
        </div>
      )}
    </div>
  );
}
