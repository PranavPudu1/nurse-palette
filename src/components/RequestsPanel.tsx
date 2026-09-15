import { useMemo, useState } from "react";
import { useNurses } from "@/hooks/useNurses";
import { useWardConfig } from "@/hooks/useWardConfig";
import { useExclusions } from "@/hooks/useExclusions";
import { useAllDayOffRequests, useDecideDayOffRequest, datesInRange, DayOffRequest } from "@/hooks/useDayOffRequests";
import { validateSchedule, scoreSchedule } from "@/lib/schedule-constraints";
import type { NurseWithLevel, WardConfig } from "@/lib/schedule-constraints";
import { ScheduleGrid } from "@/components/ScheduleGrid";
import { supabase } from "@/integrations/supabase/client";
import { useLang, monthLabel } from "@/lib/i18n";
import { Check, X, Eye, Loader2, AlertCircle, AlertTriangle } from "lucide-react";

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
};

export function RequestsPanel() {
  const { t, lang } = useLang();
  const { data: requests = [] } = useAllDayOffRequests();
  const { data: nurses = [] } = useNurses();
  const { data: wardConfigs = [] } = useWardConfig();
  const { data: exclusions = [] } = useExclusions();
  const decide = useDecideDayOffRequest();
  const [previews, setPreviews] = useState<Record<string, Preview>>({});

  const pending = requests.filter((r) => r.status === "pending");
  const decided = [...requests.filter((r) => r.status !== "pending")].reverse();

  const nurseName = useMemo(() => {
    const m: Record<string, string> = {};
    for (const n of nurses) m[n.id] = n.name;
    return m;
  }, [nurses]);

  const nursesWithLevel: NurseWithLevel[] = useMemo(
    () => nurses.map((n) => ({ id: n.id, name: n.name, level: n.level ?? 1 })),
    [nurses]
  );
  const gridNurses = useMemo(() => nurses.map((n) => ({ id: n.id, name: n.name })), [nurses]);
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
      <details>
        <summary className="text-xs text-primary cursor-pointer">{t("req.viewSchedule")}</summary>
        <div className="mt-2">
          <ScheduleGrid
            nurses={gridNurses}
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

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">{t("req.title")}</h2>
        <p className="text-sm text-muted-foreground">{t("req.subtitle")}</p>
      </div>

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
                  <div className="ml-auto flex items-center gap-2">
                    <button
                      onClick={() => runPreview(r)}
                      disabled={pv?.state === "loading"}
                      className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-secondary text-secondary-foreground hover:bg-accent disabled:opacity-50 transition-colors"
                    >
                      {pv?.state === "loading" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Eye className="w-4 h-4" />}
                      {t("req.preview")}
                    </button>
                    <button
                      onClick={() => decide.mutate({ request: r, approve: true })}
                      disabled={decide.isPending}
                      className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                    >
                      <Check className="w-4 h-4" /> {t("req.approve")}
                    </button>
                    <button
                      onClick={() => decide.mutate({ request: r, approve: false })}
                      disabled={decide.isPending}
                      className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-destructive/10 text-destructive hover:bg-destructive/20 disabled:opacity-50 transition-colors"
                    >
                      <X className="w-4 h-4" /> {t("req.deny")}
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
          <div key={r.id} className="flex items-center gap-3 text-sm py-1.5 px-2 rounded hover:bg-muted/50">
            <span className="font-medium">{nurseName[r.nurse_id] ?? r.nurse_id.slice(0, 8)}</span>
            <span className="text-muted-foreground">{r.start_date} → {r.end_date}</span>
            <span className="text-muted-foreground truncate">{r.reason || ""}</span>
            <span className={`ml-auto inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_BADGE[r.status]}`}>
              {r.status === "approved" ? t("req.approved") : t("req.denied")}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
