import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";

export interface NursePreference {
  id: string;
  nurse_id: string;
  prefers_weekend: boolean;
  prefers_night: boolean;
  prefers_weekday: boolean;
  notes: string | null;
}

export function useNursePreferences(nurseId?: string) {
  return useQuery<NursePreference | null>({
    queryKey: ["nurse_preferences", nurseId],
    enabled: !!nurseId,
    queryFn: async () => {
      const { data, error } = await supabase
        .from("nurse_preferences")
        .select("*")
        .eq("nurse_id", nurseId!)
        .maybeSingle();
      if (error) throw error;
      return data;
    },
  });
}

export function useUpsertPreferences() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (pref: { nurse_id: string; prefers_weekend: boolean; prefers_night: boolean; prefers_weekday: boolean; notes?: string }) => {
      const { error } = await supabase
        .from("nurse_preferences")
        .upsert(pref, { onConflict: "nurse_id" });
      if (error) throw error;
    },
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["nurse_preferences", vars.nurse_id] });
      toast.success("Preferences saved");
    },
    onError: (e: any) => toast.error(e.message),
  });
}

export interface NurseUnavailability {
  id: string;
  nurse_id: string;
  date: string;
  reason: string | null;
}

export function useNurseUnavailability(nurseId?: string, year?: number, month?: number) {
  return useQuery<NurseUnavailability[]>({
    queryKey: ["nurse_unavailability", nurseId, year, month],
    enabled: !!nurseId && year !== undefined && month !== undefined,
    queryFn: async () => {
      const startDate = `${year}-${String(month! + 1).padStart(2, "0")}-01`;
      const daysInMonth = new Date(year!, month! + 1, 0).getDate();
      const endDate = `${year}-${String(month! + 1).padStart(2, "0")}-${String(daysInMonth).padStart(2, "0")}`;
      const { data, error } = await supabase
        .from("nurse_unavailability")
        .select("*")
        .eq("nurse_id", nurseId!)
        .gte("date", startDate)
        .lte("date", endDate)
        .order("date");
      if (error) throw error;
      return data;
    },
  });
}

export function useAddUnavailability() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (item: { nurse_id: string; date: string; reason?: string }) => {
      const { error } = await supabase.from("nurse_unavailability").insert(item);
      if (error) throw error;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["nurse_unavailability"] });
      toast.success("Unavailability added");
    },
    onError: (e: any) => toast.error(e.message),
  });
}

export function useRemoveUnavailability() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { error } = await supabase.from("nurse_unavailability").delete().eq("id", id);
      if (error) throw error;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["nurse_unavailability"] });
      toast.success("Unavailability removed");
    },
    onError: (e: any) => toast.error(e.message),
  });
}
