import { useState, useMemo } from "react";
import {
  Nurse,
  ScheduleData,
  createInitialNurses,
  generateSchedule,
  cycleShift,
  getDaysInMonth,
  dateKey,
  ShiftType,
} from "@/lib/scheduler-data";
import { ScheduleGrid } from "@/components/ScheduleGrid";
import { MonthSelector } from "@/components/MonthSelector";
import { Legend } from "@/components/Legend";
import { Users, User } from "lucide-react";

const now = new Date();

const Index = () => {
  const [view, setView] = useState<"manager" | "nurse">("manager");
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth());
  const [nurses, setNurses] = useState<Nurse[]>(createInitialNurses);
  const [schedule, setSchedule] = useState<ScheduleData>(() =>
    generateSchedule(createInitialNurses(), year, month)
  );
  const [selectedNurse, setSelectedNurse] = useState<string>("");

  const prevMonth = () => {
    if (month === 0) { setMonth(11); setYear((y) => y - 1); }
    else setMonth((m) => m - 1);
  };
  const nextMonth = () => {
    if (month === 11) { setMonth(0); setYear((y) => y + 1); }
    else setMonth((m) => m + 1);
  };

  const handleCellClick = (nurseId: string, key: string) => {
    setSchedule((prev) => {
      const current: ShiftType = prev[nurseId]?.[key] ?? "X";
      return {
        ...prev,
        [nurseId]: { ...prev[nurseId], [key]: cycleShift(current) },
      };
    });
  };

  const handleCellClear = (nurseId: string, key: string) => {
    setSchedule((prev) => ({
      ...prev,
      [nurseId]: { ...prev[nurseId], [key]: "X" as ShiftType },
    }));
  };

  const handleAddNurse = (name: string) => {
    const id = `nurse-${Date.now()}`;
    const newNurse: Nurse = { id, name };
    setNurses((prev) => [...prev, newNurse]);
    // generate schedule for new nurse
    const days = getDaysInMonth(year, month);
    const shifts: Record<string, ShiftType> = {};
    for (let d = 1; d <= days; d++) {
      shifts[dateKey(year, month, d)] = "X";
    }
    setSchedule((prev) => ({ ...prev, [id]: shifts }));
  };

  const handleRemoveNurse = (nurseId: string) => {
    setNurses((prev) => prev.filter((n) => n.id !== nurseId));
    setSchedule((prev) => {
      const next = { ...prev };
      delete next[nurseId];
      return next;
    });
    if (selectedNurse === nurseId) setSelectedNurse("");
  };

  const filteredNurses = useMemo(() => {
    if (view === "nurse" && selectedNurse) {
      return nurses.filter((n) => n.id === selectedNurse);
    }
    return nurses;
  }, [view, selectedNurse, nurses]);

  return (
    <div className="min-h-screen bg-background">
      {/* Top bar */}
      <header className="border-b border-border bg-card px-6 py-4">
        <div className="max-w-[1600px] mx-auto flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight">Nurse Scheduler</h1>
            <p className="text-sm text-muted-foreground">Manage shifts at a glance</p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setView("manager")}
              className={`inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                view === "manager"
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-secondary-foreground hover:bg-accent"
              }`}
            >
              <Users className="w-4 h-4" />
              Manager
            </button>
            <button
              onClick={() => setView("nurse")}
              className={`inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                view === "nurse"
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-secondary-foreground hover:bg-accent"
              }`}
            >
              <User className="w-4 h-4" />
              My Schedule
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-6 py-6 flex flex-col gap-5">
        {/* Controls row */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
          <MonthSelector year={year} month={month} onPrev={prevMonth} onNext={nextMonth} />
          <div className="flex items-center gap-4">
            {view === "nurse" && (
              <select
                value={selectedNurse}
                onChange={(e) => setSelectedNurse(e.target.value)}
                className="px-3 py-2 text-sm rounded-md border border-input bg-card focus:outline-none focus:ring-2 focus:ring-ring/30"
              >
                <option value="">Select nurse…</option>
                {nurses.map((n) => (
                  <option key={n.id} value={n.id}>
                    {n.name}
                  </option>
                ))}
              </select>
            )}
            <Legend />
          </div>
        </div>

        {/* Grid */}
        {view === "nurse" && !selectedNurse ? (
          <div className="flex items-center justify-center py-20 text-muted-foreground">
            Pick a nurse above to view their schedule.
          </div>
        ) : (
          <ScheduleGrid
            nurses={filteredNurses}
            schedule={schedule}
            year={year}
            month={month}
            readOnly={view === "nurse"}
            onCellClick={handleCellClick}
            onCellClear={handleCellClear}
            onAddNurse={handleAddNurse}
            onRemoveNurse={handleRemoveNurse}
          />
        )}
      </main>
    </div>
  );
};

export default Index;
