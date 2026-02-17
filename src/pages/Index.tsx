import { useState, useMemo, useEffect, useCallback } from "react";
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
import { exportScheduleCSV } from "@/lib/export-csv";
import { ScheduleGrid } from "@/components/ScheduleGrid";
import { MonthSelector } from "@/components/MonthSelector";
import { Legend } from "@/components/Legend";
import { Users, User, Pencil, Lock, Unlock, Save, Download } from "lucide-react";
import { toast } from "sonner";

const now = new Date();

function storageKey(year: number, month: number) {
  return `nurse-schedule-${year}-${String(month + 1).padStart(2, "0")}`;
}

function loadFromStorage(year: number, month: number) {
  try {
    const raw = localStorage.getItem(storageKey(year, month));
    if (raw) return JSON.parse(raw) as { nurses: Nurse[]; schedule: ScheduleData; locked: boolean };
  } catch {}
  return null;
}

const Index = () => {
  const [view, setView] = useState<"manager" | "nurse">("manager");
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth());
  const [nurses, setNurses] = useState<Nurse[]>(createInitialNurses);
  const [schedule, setSchedule] = useState<ScheduleData>(() =>
    generateSchedule(createInitialNurses(), year, month)
  );
  const [selectedNurse, setSelectedNurse] = useState("");
  const [editMode, setEditMode] = useState(false);
  const [locked, setLocked] = useState(false);

  // Load saved data when month changes
  useEffect(() => {
    const saved = loadFromStorage(year, month);
    if (saved) {
      setNurses(saved.nurses);
      setSchedule(saved.schedule);
      setLocked(saved.locked);
    } else {
      const initial = createInitialNurses();
      setNurses(initial);
      setSchedule(generateSchedule(initial, year, month));
      setLocked(false);
    }
    setEditMode(false);
  }, [year, month]);

  const prevMonth = () => {
    if (month === 0) { setMonth(11); setYear((y) => y - 1); }
    else setMonth((m) => m - 1);
  };
  const nextMonth = () => {
    if (month === 11) { setMonth(0); setYear((y) => y + 1); }
    else setMonth((m) => m + 1);
  };

  const canEdit = view === "manager" && editMode && !locked;

  const handleCellClick = (nurseId: string, key: string) => {
    if (!canEdit) return;
    setSchedule((prev) => {
      const current: ShiftType = prev[nurseId]?.[key] ?? "X";
      return { ...prev, [nurseId]: { ...prev[nurseId], [key]: cycleShift(current) } };
    });
  };

  const handleCellClear = (nurseId: string, key: string) => {
    if (!canEdit) return;
    setSchedule((prev) => ({
      ...prev,
      [nurseId]: { ...prev[nurseId], [key]: "X" as ShiftType },
    }));
  };

  const handleAddNurse = (name: string) => {
    if (!canEdit) return;
    const id = `nurse-${Date.now()}`;
    setNurses((prev) => [...prev, { id, name }]);
    const days = getDaysInMonth(year, month);
    const shifts: Record<string, ShiftType> = {};
    for (let d = 1; d <= days; d++) shifts[dateKey(year, month, d)] = "X";
    setSchedule((prev) => ({ ...prev, [id]: shifts }));
  };

  const handleRemoveNurse = (nurseId: string) => {
    if (!canEdit) return;
    setNurses((prev) => prev.filter((n) => n.id !== nurseId));
    setSchedule((prev) => { const next = { ...prev }; delete next[nurseId]; return next; });
    if (selectedNurse === nurseId) setSelectedNurse("");
  };

  const handleSave = () => {
    localStorage.setItem(storageKey(year, month), JSON.stringify({ nurses, schedule, locked }));
    toast.success("Schedule saved");
  };

  const handleExport = () => {
    const nursesToExport = view === "nurse" && selectedNurse
      ? nurses.filter((n) => n.id === selectedNurse)
      : nurses;
    exportScheduleCSV(nursesToExport, schedule, year, month);
  };

  const filteredNurses = useMemo(() => {
    if (view === "nurse" && selectedNurse) return nurses.filter((n) => n.id === selectedNurse);
    return nurses;
  }, [view, selectedNurse, nurses]);

  return (
    <div className="min-h-screen bg-background">
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
                view === "manager" ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground hover:bg-accent"
              }`}
            >
              <Users className="w-4 h-4" /> Manager
            </button>
            <button
              onClick={() => setView("nurse")}
              className={`inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                view === "nurse" ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground hover:bg-accent"
              }`}
            >
              <User className="w-4 h-4" /> My Schedule
            </button>
          </div>
        </div>
      </header>

      {/* Locked banner */}
      {locked && (
        <div className="bg-accent border-b border-border px-6 py-2">
          <div className="max-w-[1600px] mx-auto flex items-center gap-2 text-sm font-medium text-accent-foreground">
            <Lock className="w-4 h-4" /> This month is locked — editing is disabled.
          </div>
        </div>
      )}

      <main className="max-w-[1600px] mx-auto px-6 py-6 flex flex-col gap-5">
        {/* Controls row */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
          <MonthSelector year={year} month={month} onPrev={prevMonth} onNext={nextMonth} />
          <div className="flex items-center gap-3 flex-wrap">
            {view === "nurse" && (
              <select
                value={selectedNurse}
                onChange={(e) => setSelectedNurse(e.target.value)}
                className="px-3 py-2 text-sm rounded-md border border-input bg-card focus:outline-none focus:ring-2 focus:ring-ring/30"
              >
                <option value="">Select nurse…</option>
                {nurses.map((n) => (
                  <option key={n.id} value={n.id}>{n.name}</option>
                ))}
              </select>
            )}
            <Legend />
          </div>
        </div>

        {/* Action bar */}
        <div className="flex items-center gap-2 flex-wrap">
          {view === "manager" && (
            <>
              <button
                onClick={() => setEditMode((v) => !v)}
                className={`inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  editMode
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-secondary-foreground hover:bg-accent"
                }`}
              >
                <Pencil className="w-4 h-4" />
                Edit Mode{editMode ? " ON" : ""}
              </button>
              <button
                onClick={() => setLocked((v) => !v)}
                className={`inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  locked
                    ? "bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    : "bg-secondary text-secondary-foreground hover:bg-accent"
                }`}
              >
                {locked ? <Unlock className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
                {locked ? "Unlock Month" : "Lock Month"}
              </button>
              <button
                onClick={handleSave}
                className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-secondary text-secondary-foreground hover:bg-accent transition-colors"
              >
                <Save className="w-4 h-4" /> Save
              </button>
            </>
          )}
          <button
            onClick={handleExport}
            disabled={view === "nurse" && !selectedNurse}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-secondary text-secondary-foreground hover:bg-accent disabled:opacity-40 transition-colors"
          >
            <Download className="w-4 h-4" /> Export CSV
          </button>
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
            readOnly={!canEdit}
            onCellClick={handleCellClick}
            onCellClear={handleCellClear}
            onAddNurse={canEdit ? handleAddNurse : undefined}
            onRemoveNurse={canEdit ? handleRemoveNurse : undefined}
          />
        )}
      </main>
    </div>
  );
};

export default Index;
