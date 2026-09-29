import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";

export interface Notification {
  id: string;
  nurse_id: string;
  kind: string;
  request_id: string | null;
  /** An i18n key, not a sentence: the app is bilingual and translates client-side. */
  body_key: string;
  payload: Record<string, any>;
  read_at: string | null;
  created_at: string;
}

/**
 * A nurse's notifications, newest first.
 *
 * Polled rather than pushed. Realtime would need the supabase_realtime
 * publication enabled on the project, and the rows are already shaped to drive
 * an email sender later if that is ever wanted.
 */
export function useMyNotifications(nurseId?: string) {
  return useQuery<Notification[]>({
    queryKey: ["notifications", nurseId],
    enabled: !!nurseId,
    refetchInterval: 60_000,
    queryFn: async () => {
      const { data, error } = await supabase
        .from("notifications")
        .select("*")
        .eq("nurse_id", nurseId!)
        .order("created_at", { ascending: false })
        .limit(50);
      if (error) throw error;
      return (data ?? []) as Notification[];
    },
  });
}

export function useMarkNotificationsRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (ids: string[]) => {
      if (ids.length === 0) return;
      const { error } = await supabase
        .from("notifications")
        .update({ read_at: new Date().toISOString() })
        .in("id", ids);
      if (error) throw error;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });
}
