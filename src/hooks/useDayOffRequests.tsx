import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";
import { useLang } from "@/lib/i18n";

export interface DayOffRequest {
  id: string;
  nurse_id: string;
  start_date: string;
  end_date: string;
  reason: string | null;
  /** The committed outcome. Stays "pending" until a final decision is recorded. */
  status: "pending" | "approved" | "denied";
  /** A manager's exploratory lean. Never visible to the nurse, never a decision. */
  tentative: "approve" | "deny" | null;
  tentative_at: string | null;
  decided_at: string | null;
  decided_by: string | null;
  decision_note: string | null;
  created_at: string;
}

/**
 * Every ISO date from start to end inclusive, capped at 62 days.
 *
 * All arithmetic is in UTC. Parsing "YYYY-MM-DD" as local midnight and then
 * serializing with toISOString() shifts every date back a day east of UTC,
 * which silently moved approved PTO in the Korean locale.
 */
export function datesInRange(start: string, end: string): string[] {
  const out: string[] = [];
  const d = parseUTC(start);
  const stop = parseUTC(end);
  if (!d || !stop) return out;
  while (d.getTime() <= stop.getTime() && out.length < 62) {
    out.push(d.toISOString().slice(0, 10));
    d.setUTCDate(d.getUTCDate() + 1);
  }
  return out;
}

function parseUTC(iso: string): Date | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!m) return null;
  return new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3])));
}

/** What a nurse sees of their own request: the committed outcome, not a
 *  manager's working notes. */
export type MyDayOffRequest = Pick<
  DayOffRequest,
  "id" | "nurse_id" | "start_date" | "end_date" | "reason" | "status" | "decided_at" | "decision_note" | "created_at"
>;

const MY_REQUEST_COLUMNS =
  "id, nurse_id, start_date, end_date, reason, status, decided_at, decision_note, created_at";

export function useMyDayOffRequests(nurseId?: string) {
  return useQuery<MyDayOffRequest[]>({
    queryKey: ["day_off_requests", "mine", nurseId],
    enabled: !!nurseId,
    queryFn: async () => {
      // Explicit columns, not "*": a manager's exploratory `tentative` lean is
      // theirs, and the nurse only needs the committed outcome.
      const { data, error } = await supabase
        .from("day_off_requests")
        .select(MY_REQUEST_COLUMNS)
        .eq("nurse_id", nurseId!)
        .order("created_at", { ascending: false });
      if (error) throw error;
      return (data ?? []) as MyDayOffRequest[];
    },
  });
}

export function useAllDayOffRequests() {
  return useQuery<DayOffRequest[]>({
    queryKey: ["day_off_requests", "all"],
    queryFn: async () => {
      // Oldest first: requests are decided chronologically, each against
      // the state the earlier decisions left behind (Sep 16 meeting).
      const { data, error } = await supabase
        .from("day_off_requests")
        .select("*")
        .order("created_at", { ascending: true });
      if (error) throw error;
      return (data ?? []) as DayOffRequest[];
    },
  });
}

export function useAddDayOffRequest() {
  const qc = useQueryClient();
  const { t } = useLang();
  return useMutation({
    mutationFn: async (item: { nurse_id: string; start_date: string; end_date: string; reason?: string }) => {
      const { error } = await supabase.from("day_off_requests").insert(item);
      if (error) throw error;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["day_off_requests"] });
      toast.success(t("pref.requestAdded"));
    },
    onError: (e: any) => toast.error(e.message),
  });
}

export function useWithdrawDayOffRequest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { error } = await supabase.from("day_off_requests").delete().eq("id", id);
      if (error) throw error;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["day_off_requests"] }),
    onError: (e: any) => toast.error(e.message),
  });
}

/**
 * Record a manager's exploratory lean on a request.
 *
 * Writes nothing but `tentative`: no unavailability rows, no status change, no
 * notification. This is the "scheduling exploration" half of the two-stage
 * split - the manager can lean approve on everything, look at the resulting
 * schedule, and back off without anything having happened.
 */
export function useSetTentativeDecision() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ requestId, tentative }: {
      requestId: string;
      tentative: "approve" | "deny" | null;
    }) => {
      const { error } = await supabase
        .from("day_off_requests")
        .update({
          tentative,
          tentative_at: tentative ? new Date().toISOString() : null,
        })
        .eq("id", requestId);
      if (error) throw error;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["day_off_requests"] });
    },
    onError: (e: any) => toast.error(e.message),
  });
}

/**
 * Commit the tentative decisions as final: sets the status, materializes or
 * removes the days off, and notifies each nurse.
 *
 * One RPC, so a batch is all-or-nothing. The old two-round-trip version could
 * block a nurse's days and then fail to record the decision.
 */
export function useCommitDecisions() {
  const qc = useQueryClient();
  const { t } = useLang();
  return useMutation({
    mutationFn: async (requestIds: string[]) => {
      const { data, error } = await supabase.rpc("commit_tentative_decisions", {
        p_request_ids: requestIds,
      });
      if (error) throw error;
      return (data ?? 0) as number;
    },
    onSuccess: (n) => {
      qc.invalidateQueries({ queryKey: ["day_off_requests"] });
      qc.invalidateQueries({ queryKey: ["nurse_unavailability"] });
      qc.invalidateQueries({ queryKey: ["notifications"] });
      toast.success(t("req.committedToast", { n }));
    },
    onError: (e: any) => toast.error(e.message),
  });
}

/**
 * Reopen a decided request. Deletes exactly the unavailability rows that this
 * request's approval created, leaving days a manager or nurse entered by hand
 * untouched.
 */
export function useRevertDecision() {
  const qc = useQueryClient();
  const { t } = useLang();
  return useMutation({
    mutationFn: async (requestId: string) => {
      const { error } = await supabase.rpc("revert_day_off_decision", {
        p_request_id: requestId,
      });
      if (error) throw error;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["day_off_requests"] });
      qc.invalidateQueries({ queryKey: ["nurse_unavailability"] });
      qc.invalidateQueries({ queryKey: ["notifications"] });
      toast.success(t("req.revertedToast"));
    },
    onError: (e: any) => toast.error(e.message),
  });
}

/**
 * Every nurse's approved days off in a month, for the schedule grid's solid
 * PTO markers. The per-nurse hooks cannot answer this for a manager's grid.
 */
export function useMonthUnavailability(year: number, month: number) {
  const days = new Date(year, month + 1, 0).getDate();
  const mm = String(month + 1).padStart(2, "0");
  const start = `${year}-${mm}-01`;
  const end = `${year}-${mm}-${String(days).padStart(2, "0")}`;
  return useQuery<{ nurse_id: string; date: string }[]>({
    queryKey: ["nurse_unavailability", "month", year, month],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("nurse_unavailability")
        .select("nurse_id, date")
        .gte("date", start)
        .lte("date", end);
      if (error) throw error;
      return data ?? [];
    },
  });
}

export interface UpcomingUnavailability {
  id: string;
  nurse_id: string;
  date: string;
  reason: string | null;
}

/** A nurse's upcoming approved unavailable dates (today onward), so the
 * panel is not frozen to the current calendar month. */
export function useUpcomingUnavailability(nurseId?: string) {
  return useQuery<UpcomingUnavailability[]>({
    queryKey: ["nurse_unavailability", "upcoming", nurseId],
    enabled: !!nurseId,
    queryFn: async () => {
      const today = new Date().toISOString().slice(0, 10);
      const { data, error } = await supabase
        .from("nurse_unavailability")
        .select("*")
        .eq("nurse_id", nurseId!)
        .gte("date", today)
        .order("date")
        .limit(90);
      if (error) throw error;
      return (data ?? []) as UpcomingUnavailability[];
    },
  });
}
