import { useState, useMemo, useCallback, useRef, useEffect } from "react";
import { useNurses } from "@/hooks/useNurses";
import { useSchedules, useUpsertShift } from "@/hooks/useSchedules";
import { useWardConfig } from "@/hooks/useWardConfig";
import { useExclusions } from "@/hooks/useExclusions";
import { cycleShift, dateKey, ShiftType, ScheduleData } from "@/lib/scheduler-data";
import { validateSchedule } from "@/lib/schedule-constraints";
import type { NurseWithLevel, WardConfig } from "@/lib/schedule-constraints";
import { exportScheduleCSV } from "@/lib/export-csv";
import { ScheduleGrid } from "@/components/ScheduleGrid";
import { ScheduleComparison } from "@/components/ScheduleComparison";
import { MonthSelector } from "@/components/MonthSelector";
import { Legend } from "@/components/Legend";
import { ViolationsPanel } from "@/components/ViolationsPanel";
import { Download, Wand2, Loader2, AlertTriangle } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "@/hooks/use-toast";

const now = new Date();

export function ScheduleTab() {
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth());
  const [generating, setGenerating] = useState(false);
  const [generatedOptions, setGeneratedOptions] = useState<any[] | null>(null);

  // Local overrides for immediate UI feedback
  const [localOverrides, setLocalOverrides] = useState<Record<string, Record<string, ShiftType>>>({});

  const { data: nurses = [] } = useNurses();
  const { data: serverSchedule = {}, isLoading } = useSchedules(year, month);
  const upsertShift = useUpsertShift();
  const { data: wardConfigs = [] } = useWardConfig();
  const { data: exclusions = [] } = useExclusions();

  // Clear local overrides when server data updates (meaning server caught up)
  const prevServerRef = useRef(serverSchedule);
  useEffect(() => {
    if (prevServerRef.current !== serverSchedule) {
      prevServerRef.current = serverSchedule;
      setLocalOverrides({});
    }
  }, [serverSchedule]);

  // Merge server schedule with local overrides
  const schedule: ScheduleData = useMemo(() => {
    const merged = { ...serverSchedule };
    for (const [nurseId, dates] of Object.entries(localOverrides)) {
      merged[nurseId] = { ...(merged[nurseId] ?? {}), ...dates };
    }
    return merged;
  }, [serverSchedule, localOverrides]);

  const prevMonth = () => {
    if (month === 0) { setMonth(11); setYear((y) => y - 1); }
    else setMonth((m) => m - 1);
  };
  const nextMonth = () => {
    if (month === 11) { setMonth(0); setYear((y) => y + 1); }
    else setMonth((m) => m + 1);
  };

  const handleCellClick = useCallback((nurseId: string, key: string) => {
    // Read from local overrides first, then server schedule
    const current: ShiftType =
      localOverrides[nurseId]?.[key] ??
      serverSchedule[nurseId]?.[key] ?? "X";
    const next = cycleShift(current);

    // Update local state immediately
    setLocalOverrides((prev) => ({
      ...prev,
      [nurseId]: { ...(prev[nurseId] ?? {}), [key]: next },
    }));

    // Fire mutation to server
    upsertShift.mutate({ nurseId, date: key, shiftType: next });
  }, [localOverrides, serverSchedule, upsertShift]);

  const handleCellClear = useCallback((nurseId: string, key: string) => {
    setLocalOverrides((prev) => ({
      ...prev,
      [nurseId]: { ...(prev[nurseId] ?? {}), [key]: "X" as ShiftType },
    }));
    upsertShift.mutate({ nurseId, date: key, shiftType: "X" });
  }, [upsertShift]);

  const nursesWithLevel: NurseWithLevel[] = useMemo(() =>
    nurses.map((n) => ({ id: n.id, name: n.name, level: n.level ?? 1 })),
    [nurses]
  );

  const gridNurses = useMemo(() =>
    nurses.map((n) => ({ id: n.id, name: n.name })),
    [nurses]
  );

  const mappedConfigs: WardConfig[] = useMemo(() =>
    wardConfigs.map((c) => ({
      shift_type: c.shift_type,
      required_nurses: c.required_nurses,
      level_mix: (c.level_mix && typeof c.level_mix === 'object' && !Array.isArray(c.level_mix))
        ? c.level_mix as Record<string, number>
        : {},
    })),
    [wardConfigs]
  );

  const violations = useMemo(() =>
    nursesWithLevel.length > 0
      ? validateSchedule(nursesWithLevel, schedule, year, month, mappedConfigs, exclusions)
      : [],
    [nursesWithLevel, schedule, year, month, mappedConfigs, exclusions]
  );

  const errorCount = violations.filter((v) => v.severity === "error").length;
  const warnCount = violations.filter((v) => v.severity === "warning").length;

  const handleExport = () => {
    exportScheduleCSV(gridNurses, schedule, year, month);
  };

  const handleGenerate = async () => {
    // Pre-flight check: enough accepted nurses for ward demand?
    const acceptedNurses = nurses.filter((n) => n.invite_status === "accepted");
    const totalDemand = wardConfigs.reduce((sum, c) => sum + c.required_nurses, 0);
    if (acceptedNurses.length < totalDemand) {
      toast({
        title: "Not enough nurses",
        description: `You have ${acceptedNurses.length} accepted nurse(s) but your ward config requires ${totalDemand} per day (${wardConfigs.map((c) => `${c.shift_type}: ${c.required_nurses}`).join(", ")}). Accept more nurse invites or lower the ward requirements.`,
        variant: "destructive",
      });
      return;
    }

    setGenerating(true);
    try {
      const { data, error } = await supabase.functions.invoke("generate-schedule", {
        body: { year, month },
      });
      if (error) throw error;
      if (data?.error) {
        // Parse optimizer-level errors for actionable messages
        const errMsg: string = data.error;
        if (errMsg.includes("No feasible schedule")) {
          toast({
            title: "No feasible schedule",
            description: "The optimizer couldn't satisfy all constraints. Try: reducing required nurses per shift, accepting more nurse invites, or removing some unavailability entries.",
            variant: "destructive",
          });
        } else {
          toast({ title: "Generation failed", description: errMsg, variant: "destructive" });
        }
        return;
      }
      setGeneratedOptions(data.options);
    } catch (err: any) {
      const msg = err?.message ?? String(err);
      if (msg.includes("No feasible schedule") || msg.includes("422")) {
        toast({
          title: "No feasible schedule",
          description: "The optimizer couldn't satisfy all constraints. Try: reducing required nurses per shift, accepting more nurse invites, or removing some unavailability entries.",
          variant: "destructive",
        });
      } else if (msg.includes("SCHEDULER_API_URL")) {
        toast({
          title: "Scheduler not configured",
          description: "The schedule optimizer service URL hasn't been set up yet. Contact your administrator.",
          variant: "destructive",
        });
      } else {
        toast({ title: "Generation failed", description: msg, variant: "destructive" });
      }
    } finally {
      setGenerating(false);
    }
  };

  const handleApplySchedule = async (newSchedule: Record<string, Record<string, ShiftType>>) => {
    const rows: { nurse_id: string; date: string; shift_type: string }[] = [];
    for (const [nurseId, dates] of Object.entries(newSchedule)) {
      for (const [date, shiftType] of Object.entries(dates)) {
        rows.push({ nurse_id: nurseId, date, shift_type: shiftType });
      }
    }

    const { error } = await supabase
      .from("schedules")
      .upsert(rows, { onConflict: "nurse_id,date" });

    if (error) {
      toast({ title: "Apply failed", description: error.message, variant: "destructive" });
    } else {
      toast({ title: "Schedule applied", description: "The generated schedule has been saved." });
      setGeneratedOptions(null);
      window.location.reload();
    }
  };

  if (generatedOptions) {
    return (
      <ScheduleComparison
        options={generatedOptions}
        nurses={nursesWithLevel}
        year={year}
        month={month}
        wardConfigs={mappedConfigs}
        exclusions={exclusions}
        onApply={handleApplySchedule}
        onClose={() => setGeneratedOptions(null)}
      />
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
        <MonthSelector year={year} month={month} onPrev={prevMonth} onNext={nextMonth} />
        <div className="flex items-center gap-3 flex-wrap">
          <button
            onClick={handleGenerate}
            disabled={nurses.length === 0 || generating}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-40 transition-colors"
          >
            {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
            {generating ? "Generating…" : "Auto-Generate"}
          </button>
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

      {(errorCount > 0 || warnCount > 0) && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-amber-50 border border-amber-200 text-sm">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
          <span className="text-amber-800">
            {errorCount > 0 && <span className="font-semibold text-destructive">{errorCount} errors</span>}
            {errorCount > 0 && warnCount > 0 && " · "}
            {warnCount > 0 && <span className="font-semibold text-amber-600">{warnCount} warnings</span>}
          </span>
        </div>
      )}

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
          violations={violations}
          onCellClick={handleCellClick}
          onCellClear={handleCellClear}
        />
      )}
    </div>
  );
}
