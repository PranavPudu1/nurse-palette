import { useState, useMemo, useCallback, useRef, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useNurses } from "@/hooks/useNurses";
import { useSchedules, useUpsertShift } from "@/hooks/useSchedules";
import { useWardConfig } from "@/hooks/useWardConfig";
import { useExclusions } from "@/hooks/useExclusions";
import { useAllDayOffRequests, useMonthUnavailability, datesInRange } from "@/hooks/useDayOffRequests";
import { buildTimeOffMap } from "@/lib/time-off";
import { cycleShift, dateKey, ShiftType, ScheduleData } from "@/lib/scheduler-data";
import { validateSchedule } from "@/lib/schedule-constraints";
import type { NurseWithLevel, WardConfig } from "@/lib/schedule-constraints";
import { exportScheduleCSV } from "@/lib/export-csv";
import { ScheduleGrid } from "@/components/ScheduleGrid";
import { ScheduleComparison } from "@/components/ScheduleComparison";
import type { TempVariant } from "@/components/ScheduleComparison";
import { estimateCost } from "@/lib/schedule-constraints";
import type { TempSummary } from "@/lib/variant-stats";
import { MonthSelector } from "@/components/MonthSelector";
import { Legend } from "@/components/Legend";
import { ViolationsPanel } from "@/components/ViolationsPanel";
import { NurseInfoDialog } from "@/components/NurseInfoDialog";
import { Download, Wand2, Loader2, AlertTriangle, History, CalendarClock, UserPlus } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "@/hooks/use-toast";
import { useLang } from "@/lib/i18n";

const now = new Date();

interface ScheduleTabProps {
  /** Set when the manager jumps here from the requests page to explore a set of
   *  tentative decisions. Owned by Index so it survives this tab unmounting. */
  explore?: { ids: string[]; year: number; month: number } | null;
}

export function ScheduleTab({ explore }: ScheduleTabProps = {}) {
  const { t } = useLang();
  const qc = useQueryClient();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth());
  const [generating, setGenerating] = useState(false);
  const [generatedOptions, setGeneratedOptions] = useState<any[] | null>(null);
  const [selectedNurseId, setSelectedNurseId] = useState<string | null>(null);
  // A failed generation is rendered as an inline card, not a toast: a toast
  // disappears and cannot host the "try temp nurses" follow-up button.
  const [blocked, setBlocked] = useState<{ code: string; message: string } | null>(null);
  const [tempVariants, setTempVariants] = useState<
    { variants: TempVariant[]; minFeasibleCount: number | null } | null
  >(null);

  // Local overrides for immediate UI feedback
  const [localOverrides, setLocalOverrides] = useState<Record<string, Record<string, ShiftType>>>({});

  const { data: nurses = [] } = useNurses();
  const { data: serverSchedule = {}, isLoading } = useSchedules(year, month);
  const upsertShift = useUpsertShift();
  const { data: wardConfigs = [] } = useWardConfig();
  const { data: exclusions = [] } = useExclusions();
  const { data: allRequests = [] } = useAllDayOffRequests();
  const { data: monthUnavail = [] } = useMonthUnavailability(year, month);

  // Every generation run is saved, so options survive tab switches and Apply
  // ("the generated schedules are gone... can we just save it?" - Sep 16).
  const { data: pastGens = [] } = useQuery({
    queryKey: ["schedule_generations", year, month],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("schedule_generations")
        .select("id, created_at, options")
        .eq("year", year)
        .eq("month", month)
        .order("created_at", { ascending: false })
        .limit(10);
      if (error) throw error;
      return data ?? [];
    },
  });

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

  const nursesWithLevel: NurseWithLevel[] = useMemo(() => {
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    // A window is stored as dates; the grid works in days of the displayed
    // month. A window ending in a later month places no limit on this one.
    const dayIn = (iso: string | null, edge: number): number | undefined => {
      if (!iso) return undefined;
      const [y, m] = [parseInt(iso.slice(0, 4), 10), parseInt(iso.slice(5, 7), 10) - 1];
      if (y !== year || m !== month) {
        const before = y < year || (y === year && m < month);
        // Before this month: no limit at the start, everything out at the end.
        return edge === 1 ? (before ? undefined : daysInMonth + 1)
                          : (before ? 0 : undefined);
      }
      return parseInt(iso.slice(8, 10), 10);
    };
    return nurses.map((n) => ({
      id: n.id,
      name: n.name,
      level: n.level ?? 1,
      badge: n.employment_type === "temp" ? ("temp" as const) : undefined,
      availableFrom: dayIn(n.available_from, 1),
      availableUntil: dayIn(n.available_until, -1),
    }));
  }, [nurses, year, month]);

  // ── What-if assumptions ────────────────────────────────────────────────────
  // The requests page records a manager's lean; generation here is where they
  // see what that lean actually produces. Ticking a box changes only the
  // generated schedule - never the request.
  const monthStart = `${year}-${String(month + 1).padStart(2, "0")}-01`;
  const monthEnd = `${year}-${String(month + 1).padStart(2, "0")}-${String(
    new Date(year, month + 1, 0).getDate()
  ).padStart(2, "0")}`;

  const pendingThisMonth = useMemo(
    () => allRequests.filter(
      (r) => r.status === "pending" && r.start_date <= monthEnd && r.end_date >= monthStart
    ),
    [allRequests, monthStart, monthEnd]
  );

  const [assumedIds, setAssumedIds] = useState<string[]>([]);

  // Which requests exist, as a stable value. React Query refetches on window
  // focus and hands back a fresh array each time; keying the seed effect on the
  // identity of that array would silently undo boxes the manager just ticked.
  const pendingKey = pendingThisMonth.map((r) => r.id).join(",");
  const exploreKey = explore && explore.year === year && explore.month === month
    ? explore.ids.join(",")
    : null;

  // Arriving from the requests page: adopt the month those requests are in,
  // otherwise the leanings would be applied to whatever month happened to be on
  // screen and the handoff would silently do nothing.
  useEffect(() => {
    if (!explore) return;
    setYear(explore.year);
    setMonth(explore.month);
  }, [explore]);

  // Default to the manager's recorded leanings, or to what they brought over
  // from the requests page. Re-seeds only when the month, the request set, or
  // that handoff actually changes.
  useEffect(() => {
    const fromExplore = exploreKey === null ? null : exploreKey.split(",").filter(Boolean);
    setAssumedIds(
      pendingThisMonth
        .filter((r) => (fromExplore ? fromExplore.includes(r.id) : r.tentative === "approve"))
        .map((r) => r.id)
    );
    // pendingThisMonth is read but deliberately not a dependency: pendingKey
    // stands in for it so a refetch with unchanged contents is a no-op.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingKey, exploreKey, year, month]);

  const assumedUnavailability = useMemo(() => {
    const out: { nurse_id: string; date: string }[] = [];
    for (const r of pendingThisMonth) {
      if (!assumedIds.includes(r.id)) continue;
      for (const date of datesInRange(r.start_date, r.end_date)) {
        out.push({ nurse_id: r.nurse_id, date });
      }
    }
    return out;
  }, [pendingThisMonth, assumedIds]);

  // Memoized because it feeds the variant statistics, which run validateSchedule
  // per variant - a fresh array each render would redo all of that every time.
  const assumedRequests = useMemo(
    () => pendingThisMonth
      .filter((r) => assumedIds.includes(r.id))
      .map((r) => ({
        nurse_id: r.nurse_id,
        start_date: r.start_date,
        end_date: r.end_date,
      })),
    [pendingThisMonth, assumedIds]
  );

  // Pending requests draw a dotted line, approved days a solid one, so the real
  // schedule stays the single source of truth for who is off when.
  const timeOff = useMemo(
    () => buildTimeOffMap(allRequests, monthUnavail, year, month),
    [allRequests, monthUnavail, year, month]
  );

  const nurseNames = useMemo(() => {
    const map: Record<string, string> = {};
    for (const n of nurses) map[n.id] = n.name;
    return map;
  }, [nurses]);

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
    exportScheduleCSV(nursesWithLevel, schedule, year, month);
  };

  const handleGenerate = async () => {
    // Pre-flight check: enough accepted nurses for ward demand?
    const acceptedNurses = nurses.filter((n) => n.invite_status === "accepted");
    const totalDemand = wardConfigs.reduce((sum, c) => sum + c.required_nurses, 0);
    if (acceptedNurses.length < totalDemand) {
      toast({
        title: t("toast.notEnough.title"),
        description: t("toast.notEnough.desc", {
          have: acceptedNurses.length,
          need: totalDemand,
          detail: wardConfigs.map((c) => `${c.shift_type}: ${c.required_nurses}`).join(", "),
        }),
        variant: "destructive",
      });
      return;
    }

    setGenerating(true);
    setBlocked(null);
    try {
      const { data, error } = await supabase.functions.invoke("generate-schedule", {
        body: { year, month, extra_unavailability: assumedUnavailability },
      });
      if (error) throw error;
      // The edge function reports domain failures as a 200 with a code, because
      // supabase-js discards the body of any non-2xx response.
      if (data?.error) {
        setBlocked({ code: data.code ?? "optimizer_error", message: data.error });
        return;
      }
      setGeneratedOptions(data.options);
      const { error: saveErr } = await supabase
        .from("schedule_generations")
        .insert({
          year,
          month,
          options: data.options,
          assumptions: { assumed_approved: assumedIds, temp_count: 0 },
        });
      if (!saveErr) qc.invalidateQueries({ queryKey: ["schedule_generations", year, month] });
    } catch (err: any) {
      setBlocked({ code: "unexpected", message: err?.message ?? String(err) });
    } finally {
      setGenerating(false);
    }
  };

  /**
   * Ask for schedules that become possible with 1, 2 or 3 temp nurses.
   *
   * Offered only after a provably impossible month, which is the real situation:
   * a manager finds a gap they cannot fill and hires a temp. Doing it here rather
   * than by hand means the temp's days are chosen with the whole month in view,
   * not just the one gap that happened to be noticed.
   */
  const handleGenerateWithTemps = async () => {
    setGenerating(true);
    try {
      const { data, error } = await supabase.functions.invoke("generate-schedule", {
        body: {
          year,
          month,
          mode: "temp_variants",
          temp_counts: [1, 2, 3],
          extra_unavailability: assumedUnavailability,
        },
      });
      if (error) throw error;
      if (data?.error) {
        setBlocked({ code: data.code ?? "optimizer_error", message: data.error });
        return;
      }
      const vs = (data.variants ?? []) as TempVariant[];
      setTempVariants({ variants: vs, minFeasibleCount: data.min_feasible_count ?? null });

      const firstFeasible = vs.find((v) => v.status === "feasible" && v.options.length > 0);
      if (!firstFeasible) {
        // Temps are not the bottleneck. Keep the card up and say so, rather than
        // clearing it and leaving the manager with a blank screen.
        setBlocked({ code: "temps_insufficient", message: t("temp.noneWork") });
        return;
      }
      setBlocked(null);
      setGeneratedOptions(firstFeasible.options);

      const { error: saveErr } = await supabase
        .from("schedule_generations")
        .insert({
          year,
          month,
          // The generated options are stored as jsonb.
          options: firstFeasible.options as any,
          assumptions: {
            assumed_approved: assumedIds,
            temp_count: firstFeasible.temp_count,
          },
        });
      if (!saveErr) qc.invalidateQueries({ queryKey: ["schedule_generations", year, month] });
    } catch (err: any) {
      setBlocked({ code: "unexpected", message: err?.message ?? String(err) });
    } finally {
      setGenerating(false);
    }
  };

  const handleApplySchedule = async (
    newSchedule: Record<string, Record<string, ShiftType>>,
    temps: TempSummary[] = []
  ) => {
    const rows: { nurse_id: string; date: string; shift_type: string }[] = [];
    for (const [nurseId, dates] of Object.entries(newSchedule)) {
      for (const [date, shiftType] of Object.entries(dates)) {
        rows.push({ nurse_id: nurseId, date, shift_type: shiftType });
      }
    }

    // A variant's temps have no nurses row yet, on purpose: an exploration the
    // manager discards must not leave fake colleagues behind. Applying is the
    // moment they become real, so the rows and the shifts are created together.
    if (temps.length > 0) {
      const payload = temps.map((tp) => ({
        placeholder_id: tp.id,
        name: tp.name,
        level: tp.level,
        department: "General",
        available_from: tp.dates[0] ?? null,
        available_until: tp.dates[tp.dates.length - 1] ?? null,
      }));
      const { error: rpcErr } = await supabase.rpc("apply_schedule_with_temps", {
        p_temps: payload,
        p_shifts: rows,
      });
      if (rpcErr) {
        toast({ title: t("toast.applyFailed"), description: rpcErr.message, variant: "destructive" });
        return;
      }
      toast({ title: t("toast.applied.title"), description: t("toast.appliedTemps", { n: temps.length }) });
      setGeneratedOptions(null);
      setTempVariants(null);
      qc.invalidateQueries({ queryKey: ["schedules"] });
      qc.invalidateQueries({ queryKey: ["nurses"] });
      return;
    }

    const { error } = await supabase
      .from("schedules")
      .upsert(rows, { onConflict: "nurse_id,date" });

    if (error) {
      toast({ title: t("toast.applyFailed"), description: error.message, variant: "destructive" });
    } else {
      toast({ title: t("toast.applied.title"), description: t("toast.applied.desc") });
      setGeneratedOptions(null);
      setTempVariants(null);
      qc.invalidateQueries({ queryKey: ["schedules"] });
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
        onClose={() => { setGeneratedOptions(null); setTempVariants(null); }}
        variants={tempVariants?.variants}
        minFeasibleCount={tempVariants?.minFeasibleCount}
        assumedRequests={assumedRequests}
        // The currently saved schedule, so a variant's extra cost is measured
        // against what the ward is paying today rather than against nothing.
        baselineCost={estimateCost(nursesWithLevel, schedule, year, month)}
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
            {generating ? t("sched.generating") : t("sched.generate")}
          </button>
          <button
            onClick={handleExport}
            disabled={nurses.length === 0}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-secondary text-secondary-foreground hover:bg-accent disabled:opacity-40 transition-colors"
          >
            <Download className="w-4 h-4" /> {t("sched.exportCsv")}
          </button>
          <Legend />
        </div>
      </div>

      {/* What-if assumptions. Living on the schedule tab is the point: the real
          schedule stays the single source of truth, and the banner below keeps a
          what-if from being mistaken for it. */}
      {pendingThisMonth.length > 0 && (
        <div className="rounded-md border border-border bg-muted/50 p-3 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <CalendarClock className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium">{t("sched.assumeTitle")}</span>
            <span className="text-xs text-muted-foreground">{t("sched.assumeHelp")}</span>
            <div className="ml-auto flex items-center gap-2">
              <button
                onClick={() => setAssumedIds(pendingThisMonth.map((r) => r.id))}
                className="px-2 py-1 text-xs rounded border border-border bg-card hover:bg-accent transition-colors"
              >
                {t("sched.assumeAll")}
              </button>
              <button
                onClick={() => setAssumedIds([])}
                className="px-2 py-1 text-xs rounded border border-border bg-card hover:bg-accent transition-colors"
              >
                {t("sched.assumeNone")}
              </button>
            </div>
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            {pendingThisMonth.map((r) => (
              <label key={r.id} className="inline-flex items-center gap-1.5 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={assumedIds.includes(r.id)}
                  onChange={(e) =>
                    setAssumedIds((prev) =>
                      e.target.checked ? [...prev, r.id] : prev.filter((x) => x !== r.id)
                    )
                  }
                  className="rounded border-input"
                />
                <span>{nurseNames[r.nurse_id] ?? r.nurse_id.slice(0, 8)}</span>
                <span className="text-muted-foreground text-xs">
                  {r.start_date.slice(5)} → {r.end_date.slice(5)}
                </span>
              </label>
            ))}
          </div>
          {assumedIds.length > 0 && (
            <p className="text-xs font-medium text-primary">
              {t("sched.assumeBanner", { n: assumedIds.length })}
            </p>
          )}
        </div>
      )}

      {/* A failed generation is a card, not a toast: the follow-up action for an
          impossible schedule is to try temp nurses, and that needs a button that
          stays put. */}
      {blocked && (
        <div className="rounded-md border border-destructive/40 bg-destructive/5 p-3 space-y-2">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-destructive shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-semibold text-destructive">
                {blocked.code === "infeasible"
                  ? t("toast.infeasible.title")
                  : blocked.code === "not_configured"
                    ? t("toast.notConfigured.title")
                    : blocked.code === "temps_insufficient"
                      ? t("temp.insufficientTitle")
                      : t("toast.genFailed")}
              </p>
              <p className="text-sm text-muted-foreground">
                {blocked.code === "infeasible"
                  ? t("toast.infeasible.desc")
                  : blocked.code === "not_configured"
                    ? t("toast.notConfigured.desc")
                    : blocked.message}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {blocked.code === "infeasible" && (
              <button
                onClick={handleGenerateWithTemps}
                disabled={generating}
                className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-40 transition-colors"
              >
                {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
                {t("sched.tryTemps")}
              </button>
            )}
            {blocked.code === "no_solution_found" && (
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-secondary text-secondary-foreground hover:bg-accent disabled:opacity-40 transition-colors"
              >
                {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
                {t("sched.retryLonger")}
              </button>
            )}
            <button
              onClick={() => setBlocked(null)}
              className="px-3 py-2 text-sm rounded-md bg-secondary text-secondary-foreground hover:bg-accent transition-colors"
            >
              {t("sched.dismiss")}
            </button>
          </div>
        </div>
      )}

      {pastGens.length > 0 && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <History className="w-4 h-4" />
          <span>{t("sched.pastGens")}:</span>
          <select
            value=""
            onChange={(e) => {
              const g = pastGens.find((x: any) => x.id === e.target.value);
              if (g) setGeneratedOptions(g.options as any[]);
            }}
            className="px-2 py-1.5 text-sm rounded-md border border-input bg-card focus:outline-none focus:ring-2 focus:ring-ring/30"
          >
            <option value="">…</option>
            {pastGens.map((g: any) => (
              <option key={g.id} value={g.id}>
                {t("sched.pastGenOption", {
                  time: new Date(g.created_at).toLocaleString(),
                  n: Array.isArray(g.options) ? g.options.length : 0,
                })}
              </option>
            ))}
          </select>
        </div>
      )}

      {(errorCount > 0 || warnCount > 0) && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-amber-50 border border-amber-200 text-sm">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
          <span className="text-amber-800">
            {errorCount > 0 && <span className="font-semibold text-destructive">{t("sched.nErrors", { n: errorCount })}</span>}
            {errorCount > 0 && warnCount > 0 && " · "}
            {warnCount > 0 && <span className="font-semibold text-amber-600">{t("sched.nWarnings", { n: warnCount })}</span>}
          </span>
        </div>
      )}

      {isLoading ? (
        <div className="py-12 text-center text-muted-foreground">{t("sched.loading")}</div>
      ) : nurses.length === 0 ? (
        <div className="py-12 text-center text-muted-foreground">{t("sched.addFirst")}</div>
      ) : (
        <>
          <ScheduleGrid
            nurses={nursesWithLevel}
            schedule={schedule}
            year={year}
            month={month}
            readOnly={false}
            violations={violations}
            timeOff={timeOff}
            onCellClick={handleCellClick}
            onCellClear={handleCellClear}
            onNurseNameClick={setSelectedNurseId}
          />
          <ViolationsPanel violations={violations} nurseNames={nurseNames} />
        </>
      )}

      <NurseInfoDialog
        nurse={selectedNurseId ? (() => {
          const n = nurses.find((x) => x.id === selectedNurseId);
          return n ? { id: n.id, name: n.name, level: n.level, email: n.email, phone: n.phone, department: n.department } : null;
        })() : null}
        onClose={() => setSelectedNurseId(null)}
      />
    </div>
  );
}
