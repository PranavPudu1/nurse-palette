import { useState } from "react";
import { useNurses } from "@/hooks/useNurses";
import { SoftConstraintsPanel } from "@/components/SoftConstraintsPanel";
import { useNursePreferences, useUpsertPreferences, useNurseUnavailability, useAddUnavailability, useRemoveUnavailability } from "@/hooks/useNursePreferences";
import { Checkbox } from "@/components/ui/checkbox";
import { Trash2, Plus } from "lucide-react";
import { useLang } from "@/lib/i18n";

const now = new Date();

export function NursePreferencesPanel({ nurseId }: { nurseId: string }) {
  const { t } = useLang();
  const { data: pref } = useNursePreferences(nurseId);
  const upsert = useUpsertPreferences();

  const [year] = useState(now.getFullYear());
  const [month] = useState(now.getMonth());
  const { data: unavails = [] } = useNurseUnavailability(nurseId, year, month);
  const addUnavail = useAddUnavailability();
  const removeUnavail = useRemoveUnavailability();

  const [newDate, setNewDate] = useState("");
  const [newReason, setNewReason] = useState("");

  const toggle = (field: "prefers_weekend" | "prefers_night" | "prefers_weekday") => {
    upsert.mutate({
      nurse_id: nurseId,
      prefers_weekend: pref?.prefers_weekend ?? false,
      prefers_night: pref?.prefers_night ?? false,
      prefers_weekday: pref?.prefers_weekday ?? false,
      notes: pref?.notes ?? undefined,
      [field]: !(pref?.[field] ?? false),
    });
  };

  const handleAddUnavail = () => {
    if (!newDate) return;
    addUnavail.mutate({ nurse_id: nurseId, date: newDate, reason: newReason || undefined });
    setNewDate("");
    setNewReason("");
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold mb-3">{t("pref.title")}</h3>
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm">
            <Checkbox checked={pref?.prefers_weekend ?? false} onCheckedChange={() => toggle("prefers_weekend")} />
            {t("pref.weekend")}
          </label>
          <label className="flex items-center gap-2 text-sm">
            <Checkbox checked={pref?.prefers_weekday ?? false} onCheckedChange={() => toggle("prefers_weekday")} />
            {t("pref.weekday")}
          </label>
          <label className="flex items-center gap-2 text-sm">
            <Checkbox checked={pref?.prefers_night ?? false} onCheckedChange={() => toggle("prefers_night")} />
            {t("pref.night")}
          </label>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold mb-3">{t("pref.unavail")}</h3>
        <div className="flex items-end gap-2 mb-3">
          <div>
            <label className="text-xs text-muted-foreground">{t("pref.date")}</label>
            <input type="date" value={newDate} onChange={e => setNewDate(e.target.value)}
              className="block px-3 py-2 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30" />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">{t("pref.reason")}</label>
            <input type="text" value={newReason} onChange={e => setNewReason(e.target.value)} placeholder={t("pref.reasonPh")}
              className="block px-3 py-2 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30" />
          </div>
          <button onClick={handleAddUnavail} disabled={!newDate}
            className="inline-flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors">
            <Plus className="w-4 h-4" /> {t("pref.add")}
          </button>
        </div>
        {unavails.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("pref.noUnavail")}</p>
        ) : (
          <div className="space-y-1">
            {unavails.map(u => (
              <div key={u.id} className="flex items-center gap-3 text-sm py-1 px-2 rounded hover:bg-muted/50">
                <span className="font-medium">{u.date}</span>
                <span className="text-muted-foreground">{u.reason || "—"}</span>
                <button onClick={() => removeUnavail.mutate(u.id)} className="ml-auto p-1 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive">
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <SoftConstraintsPanel nurseId={nurseId} />
    </div>
  );
}
