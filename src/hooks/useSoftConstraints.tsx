import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";

export interface SoftConstraint {
  id: string;
  department: string;
  constraint_type: string;
  nurse_id: string | null;
  params: Record<string, any>;
  created_at: string;
}

export function useSoftConstraints(department = "General") {
  return useQuery<SoftConstraint[]>({
    queryKey: ["soft_constraints", department],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("soft_constraints")
        .select("*")
        .eq("department", department)
        .order("created_at");
      if (error) throw error;
      return (data ?? []) as SoftConstraint[];
    },
  });
}

export function useNurseSoftConstraints(nurseId: string) {
  return useQuery<SoftConstraint[]>({
    queryKey: ["soft_constraints", "nurse", nurseId],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("soft_constraints")
        .select("*")
        .eq("nurse_id", nurseId)
        .order("created_at");
      if (error) throw error;
      return (data ?? []) as SoftConstraint[];
    },
  });
}

export function useAddSoftConstraint() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: { department?: string; constraint_type: string; nurse_id?: string; params: Record<string, any> }) => {
      const { error } = await supabase
        .from("soft_constraints")
        .insert({
          department: input.department ?? "General",
          constraint_type: input.constraint_type,
          nurse_id: input.nurse_id ?? null,
          params: input.params,
        });
      if (error) throw error;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["soft_constraints"] });
      toast.success("Soft constraint added");
    },
    onError: (e: any) => toast.error(e.message),
  });
}

export function useRemoveSoftConstraint() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { error } = await supabase
        .from("soft_constraints")
        .delete()
        .eq("id", id);
      if (error) throw error;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["soft_constraints"] });
      toast.success("Soft constraint removed");
    },
    onError: (e: any) => toast.error(e.message),
  });
}
