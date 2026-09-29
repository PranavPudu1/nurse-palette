import { useMemo, useState } from "react";
import { useNurses } from "@/hooks/useNurses";
import { useWardConfig } from "@/hooks/useWardConfig";
import { useExclusions } from "@/hooks/useExclusions";
import {
  useAllDayOffRequests,
  useSetTentativeDecision,
  useCommitDecisions,
  useRevertDecision,
  datesInRange,
  DayOffRequest,
} from "@/hooks/useDayOffRequests";
import { validateSchedule, scoreSchedule } from "@/lib/schedule-constraints";
import type { NurseWithLevel, WardConfig } from "@/lib/schedule-constraints";
import { ScheduleGrid } from "@/components/ScheduleGrid";
import { ViolationsPanel } from "@/components/ViolationsPanel";
import { supabase } from "@/integrations/supabase/client";
import { useLang, monthLabel } from "@/lib/i18n";
import { Check, X, Eye, Loader2, AlertCircle, AlertTriangle, Gavel, Minus, RotateCcw, Info } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

interface PreviewSide {
  schedule: Record<string, Record<string, any>>;
  errors: number;
  warnings: number;
  total: number;
  violations: any[];
}

type Preview =
  | { state: "loading" }
  | { state: "error"; message: string }
  | { state: "done"; year: number; month: number; deny: PreviewSide; approve: PreviewSide };

const STATUS_BADGE: Record<string, string> = {
  approved: "bg-green-100 text-green-700",
  denied: "bg-red-100 text-red-700",
  pending: "bg-amber-100 text-amber-700",
};

interface Props {
  /** Hands the current leanings to the schedule tab, where the real schedule lives. */
  onExplore?: (ids: string[], year: number, month: number) => void;
}

export function RequestsPanel({ onExplore }: Props = {}) {
  const { t, lang } = useLang();
  const { data: requests = [] } = useAllDayOffRequests();
  const { data: nurses = [] } = useNurses();
  const { data: wardConfigs = [] } = useWardConfig();
  const { data: exclusions = [] } = useExclusions();
  const setTentative = useSetTentativeDecision();
  const commit = useCommitDecisions();
  const revert = useRevertDecision();
  const [previews, setPreviews] = useState<Record<string, Preview>>({});
  const [confirming, setConfirming] = useState<DayOffRequest[] | null>(null);

  const pending = requests.filter((r) => r.status === "pending");
  const decided = [...requests.filter((r) => r.status !== "pending")].reverse();
  const leaning = pending.filter((r) => r.tentative !== null);

  const nurseName = useMemo(() => {
    const m: Record<string, string> = {};
    for (const n of nurses) m[n.id] = n.name;
    return m;
  }, [nurses]);

  const nursesWithLevel: NurseWithLevel[] = useMemo(
    () => nurses.map((n) => ({
      id: n.id,
      name: n.name,
      level: n.level ?? 1,
      badge: n.employment_type === "temp" ? ("temp" as const) : undefined,
    })),
    [nurses]
  );
  const mappedConfigs: WardConfig[] = useMemo(
    () =>
      wardConfigs.map((c) => ({
        shift_type: c.shift_type,
        required_nurses: c.required_nurses,
        level_mix:
          c.level_mix && typeof c.level_mix === "object" && !Array.isArray(c.level_mix)
            ? (c.level_mix as Record<string, number>)
            : {},
      })),
    [wardConfigs]
  );

  const evaluate = (schedule: any, year: number, month: number): PreviewSide => {
    const violations = validateSchedule(nursesWithLevel, schedule, year, month, mappedConfigs, exclusions);
    const score = scoreSchedule(nursesWithLevel, schedule, year, month, mappedConfigs, exclusions);
    return {
      schedule,
      violations,
      errors: violations.filter((v) => v.severity === "error").length,
      warnings: violations.filter((v) => v.severity === "warning").length,
      total: score.total,
    };
  };

  const runPreview = async (req: DayOffRequest) => {
    const year = parseInt(req.start_date.slice(0, 4), 10);
    const month = parseInt(req.start_date.slice(5, 7), 10) - 1;
    setPreviews((p) => ({ ...p, [req.id]: { state: "loading" } }));
    try {
      const extra = datesInRange(req.start_date, req.end_date).map((date) => ({
        nurse_id: req.nurse_id,
        date,
      }));
      const [denyRes, approveRes] = await Promise.all([
        supabase.functions.invoke("generate-schedule", { body: { year, month, num_options: 1 } }),
        supabase.functions.invoke("generate-schedule", {
          body: { year, month, num_options: 1, extra_unavailability: extra },
        }),
      ]);
      for (const r of [denyRes, approveRes]) {
        if (r.error) throw new Error(r.error.message ?? String(r.error));
        if (r.data?.error) throw new Error(r.data.error);
      }
      const denySchedule = denyRes.data?.options?.[0]?.schedule;
      const approveSchedule = approveRes.data?.options?.[0]?.schedule;
      if (!denySchedule || !approveSchedule) throw new Error("empty result");
      setPreviews((p) => ({
        ...p,
        [req.id]: {
          state: "done",
          year,
          month,
          deny: evaluate(denySchedule, year, month),
          approve: evaluate(approveSchedule, year, month),
        },
      }));
    } catch (e: any) {
      setPreviews((p) => ({ ...p, [req.id]: { state: "error", message: e?.message ?? String(e) } }));
    }
  };

  const days = (r: DayOffRequest) => datesInRange(r.start_date, r.end_date).length;

  const sideCard = (label: string, side: PreviewSide, year: number, month: number) => (
    <div className="rounded-lg border border-border bg-card p-3 space-y-2">
      <div className="text-sm font-semibold">{label}</div>
      <div className="flex items-center gap-3 text-xs">
        <span className="inline-flex items-center gap-1 text-destructive font-medium">
          <AlertCircle className="w-3.5 h-3.5" /> {t("cmp.nErrorsHard", { n: side.errors })}
        </span>
        <span className="inline-flex items-center gap-1 text-amber-600 font-medium">
          <AlertTriangle className="w-3.5 h-3.5" /> {t("cmp.nWarningsSoft", { n: side.warnings })}
        </span>
        <span className="ml-auto font-bold text-foreground">{t("cmp.score", { n: side.total })}</span>
      </div>
      {/* The counts alone were not actionable - "three warnings" said nothing
          about which three. ViolationsPanel already writes each one out. */}
      <ViolationsPanel violations={side.violations} nurseNames={nurseName} />
      <details>
        <summary className="text-xs text-primary cursor-pointer">{t("req.viewSchedule")}</summary>
        <div className="mt-2">
          <ScheduleGrid
            nurses={nursesWithLevel}
            schedule={side.schedule}
            year={year}
            month={month}
            readOnly={true}
            violations={side.violations}
          />
        </div>
      </details>
    </div>
  );

  const leanButton = (
    r: DayOffRequest,
    value: "approve" | "deny" | null,
    icon: React.ReactNode,
    label: string,
    activeCls: string
  ) => {
    const active = r.tentative === value;
    return (
      <button
        onClick={() => setTentative.mutate({ requestId: r.id, tentative: value })}
        disabled={setTentative.isPending}
        className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-md border transition-colors disabled:opacity-50 ${
          active ? activeCls : "border-border bg-card text-muted-foreground hover:bg-accent"
        }`}
      >
        {icon} {label}
      </button>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">{t("req.title")}</h2>
        <p className="text-sm text-muted-foreground">{t("req.subtitle")}</p>
      </div>

      {/* Where the two stages are explained, once, rather than per request. */}
      {pending.length > 0 && (
        <div className="flex flex-wrap items-center gap-3 px-3 py-2.5 rounded-md bg-muted/60 border border-border text-sm">
          <span className="text-muted-foreground">
            {t("req.tallyLeaning", {
              approve: pending.filter((r) => r.tentative === "approve").length,
              deny: pending.filter((r) => r.tentative === "deny").length,
              undecided: pending.filter((r) => r.tentative === null).length,
            })}
          </span>
          <Tooltip delayDuration={100}>
            <TooltipTrigger asChild>
              <span className="cursor-help"><Info className="w-3.5 h-3.5 text-muted-foreground/70" /></span>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-[280px] text-xs">
              {t("req.exploreHelp")}
            </TooltipContent>
          </Tooltip>
          {onExplore && (
            <button
              onClick={() => {
                const assumed = pending.filter((r) => r.tentative === "approve");
                // Follow the requests actually being explored; fall back to the
                // oldest pending one when nothing has been leaned on yet.
                const anchor = assumed[0] ?? pending[0];
                onExplore(
                  assumed.map((r) => r.id),
                  parseInt(anchor.start_date.slice(0, 4), 10),
                  parseInt(anchor.start_date.slice(5, 7), 10) - 1
                );
              }}
              className="text-primary hover:underline font-medium"
            >
              {t("req.exploreOnSchedule")}
            </button>
          )}
          <button
            onClick={() => setConfirming(leaning)}
            disabled={leaning.length === 0 || commit.isPending}
            title={leaning.length === 0 ? t("req.noLeanings") : undefined}
            className="ml-auto inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-40 transition-colors"
          >
            <Gavel className="w-4 h-4" /> {t("req.recordFinalN", { n: leaning.length })}
          </button>
        </div>
      )}

      <div className="space-y-3">
        <h3 className="text-sm font-semibold">{t("req.pending")} ({pending.length})</h3>
        {pending.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("req.nonePending")}</p>
        ) : (
          pending.map((r) => {
            const pv = previews[r.id];
            return (
              <div key={r.id} className="rounded-lg border border-border bg-card p-4 space-y-3">
                <div className="flex flex-wrap items-center gap-3">
                  <div className="min-w-0">
                    <div className="text-sm font-semibold">{nurseName[r.nurse_id] ?? r.nurse_id.slice(0, 8)}</div>
                    <div className="text-sm text-muted-foreground">
                      {r.start_date} → {r.end_date} · {t("req.days", { n: days(r) })}
                      {r.reason ? ` · ${r.reason}` : ""}
                    </div>
                    <div className="text-xs text-muted-foreground/70">
                      {t("req.submitted", { date: r.created_at.slice(0, 10) })}
                    </div>
                  </div>
                  <div className="ml-auto flex items-center gap-2 flex-wrap">
                    {/* Exploration, not decision: these only move what-if schedules. */}
                    {leanButton(r, "approve", <Check className="w-3.5 h-3.5" />, t("req.exploreApprove"),
                      "border-primary bg-primary/10 text-primary")}
                    {leanButton(r, "deny", <X className="w-3.5 h-3.5" />, t("req.exploreDeny"),
                      "border-destructive bg-destructive/10 text-destructive")}
                    {leanButton(r, null, <Minus className="w-3.5 h-3.5" />, t("req.exploreClear"),
                      "border-border bg-muted text-foreground")}
                    <button
                      onClick={() => runPreview(r)}
                      disabled={pv?.state === "loading"}
                      className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-secondary text-secondary-foreground hover:bg-accent disabled:opacity-50 transition-colors"
                    >
                      {pv?.state === "loading" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Eye className="w-4 h-4" />}
                      {t("req.preview")}
                    </button>
                    <button
                      onClick={() => setConfirming([r])}
                      disabled={r.tentative === null || commit.isPending}
                      title={r.tentative === null ? t("req.noLeanings") : undefined}
                      className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-40 transition-colors"
                    >
                      <Gavel className="w-4 h-4" /> {t("req.recordFinal")}
                    </button>
                  </div>
                </div>

                {pv?.state === "loading" && (
                  <p className="text-sm text-muted-foreground">{t("req.solving")}</p>
                )}
                {pv?.state === "error" && (
                  <p className="text-sm text-destructive">{t("req.previewFailed", { msg: pv.message })}</p>
                )}
                {pv?.state === "done" && (
                  <div className="space-y-2">
                    <p className="text-xs text-muted-foreground">
                      {t("req.previewNote", { month: monthLabel(lang, pv.year, pv.month) })}
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {sideCard(t("req.ifDeny"), pv.deny, pv.year, pv.month)}
                      {sideCard(t("req.ifApprove"), pv.approve, pv.year, pv.month)}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold">{t("req.history")} ({decided.length})</h3>
        {decided.map((r) => (
          <div key={r.id} className="flex flex-wrap items-center gap-3 text-sm py-1.5 px-2 rounded hover:bg-muted/50">
            <span className="font-medium">{nurseName[r.nurse_id] ?? r.nurse_id.slice(0, 8)}</span>
            <span className="text-muted-foreground">{r.start_date} → {r.end_date}</span>
            <span className="text-muted-foreground truncate">{r.reason || ""}</span>
            {r.decided_at && (
              <span className="text-xs text-muted-foreground/70">
                {t("req.decidedOn", { date: r.decided_at.slice(0, 10) })}
              </span>
            )}
            <span className={`ml-auto inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_BADGE[r.status]}`}>
              {r.status === "approved" ? t("req.approved") : t("req.denied")}
            </span>
            <button
              onClick={() => {
                if (confirm(t("req.confirmRevert", {
                  name: nurseName[r.nurse_id] ?? "",
                  start: r.start_date,
                  end: r.end_date,
                }))) revert.mutate(r.id);
              }}
              disabled={revert.isPending}
              className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground disabled:opacity-50"
            >
              <RotateCcw className="w-3.5 h-3.5" /> {t("req.changeDecision")}
            </button>
          </div>
        ))}
      </div>

      {/* Committing notifies people, so it names exactly who and what first. */}
      {confirming && confirming.length > 0 && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-lg bg-card border border-border shadow-lg p-5 space-y-4">
            <h3 className="text-base font-semibold">{t("req.confirmTitle")}</h3>
            <p className="text-sm text-muted-foreground">{t("req.confirmBody")}</p>
            <ul className="space-y-1 text-sm max-h-48 overflow-auto">
              {confirming.map((r) => (
                <li key={r.id} className="flex items-center gap-2">
                  <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-semibold ${
                    r.tentative === "approve" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                  }`}>
                    {r.tentative === "approve" ? t("req.approved") : t("req.denied")}
                  </span>
                  <span className="font-medium">{nurseName[r.nurse_id] ?? r.nurse_id.slice(0, 8)}</span>
                  <span className="text-muted-foreground">{r.start_date} → {r.end_date}</span>
                </li>
              ))}
            </ul>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setConfirming(null)}
                className="px-3 py-2 text-sm rounded-md bg-secondary text-secondary-foreground hover:bg-accent transition-colors"
              >
                {t("req.confirmCancel")}
              </button>
              <button
                onClick={() => {
                  commit.mutate(confirming.map((r) => r.id));
                  setConfirming(null);
                }}
                disabled={commit.isPending}
                className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                <Gavel className="w-4 h-4" /> {t("req.confirmGo")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
