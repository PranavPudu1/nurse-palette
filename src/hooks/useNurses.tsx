import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";

export interface DbNurse {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  department: string | null;
  user_id: string | null;
  invite_status: string;
  created_at: string;
  updated_at: string;
}

export function useNurses() {
  return useQuery<DbNurse[]>({
    queryKey: ["nurses"],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("nurses")
        .select("*")
        .order("name");
      if (error) throw error;
      return data;
    },
  });
}

export function useAddNurse() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (nurse: { name: string; email?: string; phone?: string; department?: string }) => {
      const payload = {
        ...nurse,
        email: nurse.email?.trim().toLowerCase() || null,
      };
      const { data, error } = await supabase.from("nurses").insert(payload).select().single();
      if (error) throw error;
      return data;
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["nurses"] }); toast.success("Nurse added"); },
    onError: (e: any) => toast.error(e.message),
  });
}

export function useUpdateNurse() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...updates }: { id: string; name?: string; email?: string; phone?: string; department?: string }) => {
      const payload = {
        ...updates,
        email: updates.email?.trim().toLowerCase() || null,
      };
      const { error } = await supabase.from("nurses").update(payload).eq("id", id);
      if (error) throw error;
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["nurses"] }); toast.success("Nurse updated"); },
    onError: (e: any) => toast.error(e.message),
  });
}

export function useRemoveNurse() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { error } = await supabase.from("nurses").delete().eq("id", id);
      if (error) throw error;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["nurses"] });
      qc.invalidateQueries({ queryKey: ["schedules"] });
      toast.success("Nurse removed");
    },
    onError: (e: any) => toast.error(e.message),
  });
}
