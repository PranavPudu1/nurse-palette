import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";

export interface WardShiftConfig {
  id: string;
  department: string;
  shift_type: string;
  required_nurses: number;
  level_mix: Record<string, number>;
}

export function useWardConfig(department = "General") {
  return useQuery<WardShiftConfig[]>({
    queryKey: ["ward_shift_config", department],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("ward_shift_config")
        .select("*")
        .eq("department", department)
        .order("shift_type");
      if (error) throw error;
      return (data ?? []).map(d => ({
        ...d,
        level_mix: (typeof d.level_mix === "object" && d.level_mix !== null ? d.level_mix : {}) as Record<string, number>,
      }));
    },
  });
}

export function useUpdateWardConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, required_nurses, level_mix }: { id: string; required_nurses: number; level_mix: Record<string, number> }) => {
      const { error } = await supabase
        .from("ward_shift_config")
        .update({ required_nurses, level_mix })
        .eq("id", id);
      if (error) throw error;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ward_shift_config"] });
      toast.success("Ward config updated");
    },
    onError: (e: any) => toast.error(e.message),
  });
}
