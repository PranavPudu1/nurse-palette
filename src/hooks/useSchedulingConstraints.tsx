import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";

export interface SchedulingConstraints {
  id: string;
  department: string;
  max_shifts_per_day: number;
  night_window_max: number;
  night_window_k: number;
  days_off_after_night_block: number;
  max_consecutive_workdays: number;
  consec_trigger: number;
  days_off_after_consec: number;
}

export function useSchedulingConstraints(department = "General") {
  return useQuery<SchedulingConstraints | null>({
    queryKey: ["scheduling_constraints", department],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("scheduling_constraints")
        .select("*")
        .eq("department", department)
        .single();
      if (error) throw error;
      return data as SchedulingConstraints;
    },
  });
}

export function useUpdateSchedulingConstraints() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (params: Partial<SchedulingConstraints> & { id: string }) => {
      const { id, ...updates } = params;
      const { error } = await supabase
        .from("scheduling_constraints")
        .update(updates)
        .eq("id", id);
      if (error) throw error;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["scheduling_constraints"] });
      toast.success("Scheduling rules updated");
    },
    onError: (e: any) => toast.error(e.message),
  });
}
