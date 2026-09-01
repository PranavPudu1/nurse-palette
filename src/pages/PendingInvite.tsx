import { useAuth } from "@/hooks/useAuth";
import { useUserRole, PendingInvite } from "@/hooks/useUserRole";
import { supabase } from "@/integrations/supabase/client";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useState } from "react";
import { Check, LogOut, Mail } from "lucide-react";
import { useLang } from "@/lib/i18n";

const PendingInvitePage = () => {
  const { t } = useLang();
  const { user, signOut } = useAuth();
  const { data: roleData } = useUserRole();
  const qc = useQueryClient();
  const [accepting, setAccepting] = useState(false);

  const invite = roleData?.invite;

  const handleAccept = async () => {
    if (!invite || !user) return;
    setAccepting(true);
    try {
      const { error } = await supabase
        .from("nurses")
        .update({ user_id: user.id, invite_status: "accepted" })
        .eq("id", invite.id);
      if (error) throw error;
      toast.success(t("invite.accepted"));
      qc.invalidateQueries({ queryKey: ["user-role"] });
      qc.invalidateQueries({ queryKey: ["nurses"] });
    } catch (err: any) {
      toast.error(err.message || t("invite.acceptFailed"));
    } finally {
      setAccepting(false);
    }
  };

  if (!invite) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <div className="text-center space-y-4">
          <p className="text-muted-foreground">{t("invite.none")}</p>
          <button onClick={signOut} className="text-sm text-primary hover:underline">{t("app.signOut")}</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <div className="mx-auto w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center mb-4">
            <Mail className="w-7 h-7 text-primary" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">{t("invite.title")}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {t("invite.subtitle")}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">{t("invite.name")}</span>
            <span className="font-medium">{invite.name}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">{t("invite.dept")}</span>
            <span className="font-medium">{invite.department || "General"}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">{t("invite.email")}</span>
            <span className="font-medium">{invite.email}</span>
          </div>
        </div>

        <button
          onClick={handleAccept}
          disabled={accepting}
          className="w-full h-10 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors inline-flex items-center justify-center gap-2"
        >
          <Check className="w-4 h-4" />
          {accepting ? t("invite.accepting") : t("invite.accept")}
        </button>

        <p className="text-center">
          <button onClick={signOut} className="text-sm text-muted-foreground hover:text-foreground inline-flex items-center gap-1.5">
            <LogOut className="w-3.5 h-3.5" /> {t("app.signOut")}
          </button>
        </p>
      </div>
    </div>
  );
};

export default PendingInvitePage;
