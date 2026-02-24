import { useState, useMemo } from "react";
import { useNurses } from "@/hooks/useNurses";
import { useSchedules, useUpsertShift } from "@/hooks/useSchedules";
import { cycleShift, dateKey, ShiftType } from "@/lib/scheduler-data";
import { exportScheduleCSV } from "@/lib/export-csv";
import { ScheduleGrid } from "@/components/ScheduleGrid";
import { MonthSelector } from "@/components/MonthSelector";
import { Legend } from "@/components/Legend";
import { Download } from "lucide-react";

const now = new Date();

export function ScheduleTab() {
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth());

  const { data: nurses = [] } = useNurses();
  const { data: schedule = {}, isLoading } = useSchedules(year, month);
  const upsertShift = useUpsertShift();

  const prevMonth = () => {
    if (month === 0) { setMonth(11); setYear((y) => y - 1); }
    else setMonth((m) => m - 1);
  };
  const nextMonth = () => {
    if (month === 11) { setMonth(0); setYear((y) => y + 1); }
    else setMonth((m) => m + 1);
  };

  const handleCellClick = (nurseId: string, key: string) => {
    const current: ShiftType = schedule[nurseId]?.[key] ?? "X";
    const next = cycleShift(current);
    upsertShift.mutate({ nurseId, date: key, shiftType: next });
  };

  const handleCellClear = (nurseId: string, key: string) => {
    upsertShift.mutate({ nurseId, date: key, shiftType: "X" });
  };

  const gridNurses = useMemo(() =>
    nurses.map((n) => ({ id: n.id, name: n.name })),
    [nurses]
  );

  const handleExport = () => {
    exportScheduleCSV(gridNurses, schedule, year, month);
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
        <MonthSelector year={year} month={month} onPrev={prevMonth} onNext={nextMonth} />
        <div className="flex items-center gap-3 flex-wrap">
          <button
            onClick={handleExport}
            disabled={nurses.length === 0}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-secondary text-secondary-foreground hover:bg-accent disabled:opacity-40 transition-colors"
          >
            <Download className="w-4 h-4" /> Export CSV
          </button>
          <Legend />
        </div>
      </div>

      {isLoading ? (
        <div className="py-12 text-center text-muted-foreground">Loading schedule…</div>
      ) : nurses.length === 0 ? (
        <div className="py-12 text-center text-muted-foreground">Add nurses in the Nurses tab first.</div>
      ) : (
        <ScheduleGrid
          nurses={gridNurses}
          schedule={schedule}
          year={year}
          month={month}
          readOnly={false}
          onCellClick={handleCellClick}
          onCellClear={handleCellClear}
        />
      )}
    </div>
  );
}
