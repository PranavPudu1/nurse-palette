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
  status: "pending" | "approved" | "denied";
  decided_at: string | null;
  created_at: string;
}

/** Every ISO date from start to end inclusive, capped at 62 days. */
export function datesInRange(start: string, end: string): string[] {
  const out: string[] = [];
  const d = new Date(start + "T00:00:00");
  const stop = new Date(end + "T00:00:00");
  while (d <= stop && out.length < 62) {
    out.push(d.toISOString().slice(0, 10));
    d.setDate(d.getDate() + 1);
  }
  return out;
}

export function useMyDayOffRequests(nurseId?: string) {
  return useQuery<DayOffRequest[]>({
    queryKey: ["day_off_requests", "mine", nurseId],
    enabled: !!nurseId,
    queryFn: async () => {
      const { data, error } = await supabase
        .from("day_off_requests")
        .select("*")
        .eq("nurse_id", nurseId!)
        .order("created_at", { ascending: false });
      if (error) throw error;
      return (data ?? []) as DayOffRequest[];
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

export function useDecideDayOffRequest() {
  const qc = useQueryClient();
  const { t } = useLang();
  return useMutation({
    mutationFn: async ({ request, approve }: { request: DayOffRequest; approve: boolean }) => {
      if (approve) {
        // Approval materializes into nurse_unavailability, so the optimizer
        // path is untouched: approved days are hard constraints, pending and
        // denied requests never reach it.
        const rows = datesInRange(request.start_date, request.end_date).map((date) => ({
          nurse_id: request.nurse_id,
          date,
          reason: request.reason || "approved day off",
        }));
        const { error: upsertErr } = await supabase
          .from("nurse_unavailability")
          .upsert(rows, { onConflict: "nurse_id,date" });
        if (upsertErr) throw upsertErr;
      }
      const { error } = await supabase
        .from("day_off_requests")
        .update({ status: approve ? "approved" : "denied", decided_at: new Date().toISOString() })
        .eq("id", request.id);
      if (error) throw error;
      return approve;
    },
    onSuccess: (approve) => {
      qc.invalidateQueries({ queryKey: ["day_off_requests"] });
      qc.invalidateQueries({ queryKey: ["nurse_unavailability"] });
      toast.success(approve ? t("req.approvedToast") : t("req.deniedToast"));
    },
    onError: (e: any) => toast.error(e.message),
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
