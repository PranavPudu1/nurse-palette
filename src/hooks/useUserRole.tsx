import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/useAuth";

export type UserRole = "manager" | "nurse" | "pending" | "unknown";

export interface PendingInvite {
  id: string;
  name: string;
  department: string | null;
  email: string | null;
}

export function useUserRole() {
  const { user } = useAuth();

  return useQuery<{ role: UserRole; invite?: PendingInvite }>({
    queryKey: ["user-role", user?.id],
    enabled: !!user,
    queryFn: async () => {
      const userEmail = user?.email?.trim();

      // Check if manager
      const { data: isManager } = await supabase.rpc("is_manager");
      if (isManager) return { role: "manager" as UserRole };

      // Check if accepted nurse
      const { data: acceptedNurse } = await supabase
        .from("nurses")
        .select("id, name, department, email, invite_status")
        .eq("user_id", user!.id)
        .eq("invite_status", "accepted")
        .maybeSingle();

      if (acceptedNurse) return { role: "nurse" as UserRole };

      // Check for pending invite matching current auth email
      if (userEmail) {
        const { data: pendingInvite } = await supabase
          .from("nurses")
          .select("id, name, department, email")
          .eq("invite_status", "pending")
          .ilike("email", userEmail)
          .maybeSingle();

        if (pendingInvite) {
          return {
            role: "pending" as UserRole,
            invite: pendingInvite as PendingInvite,
          };
        }
      }

      return { role: "unknown" as UserRole };
    },
  });
}
