import { useState } from "react";
import { SoftConstraintsPanel } from "@/components/SoftConstraintsPanel";
import { useNursePreferences, useUpsertPreferences, useNurseUnavailability, useAddUnavailability, useRemoveUnavailability } from "@/hooks/useNursePreferences";
import { useMyDayOffRequests, useAddDayOffRequest, useWithdrawDayOffRequest, useUpcomingUnavailability } from "@/hooks/useDayOffRequests";
import { Checkbox } from "@/components/ui/checkbox";
import { Trash2, Plus, Send } from "lucide-react";
import { useLang } from "@/lib/i18n";

const now = new Date();

const STATUS_BADGE: Record<string, string> = {
  pending: "bg-amber-100 text-amber-700",
  approved: "bg-green-100 text-green-700",
  denied: "bg-red-100 text-red-700",
};

/**
 * manager=true (the NurseInfoDialog): direct add/remove of unavailable dates,
 * exactly as before - a manager's edit needs no approval.
 * manager=false (the nurse's own Preferences tab): unavailability goes through
 * a day-off REQUEST (date range + status) that the manager approves or
 * denies; approved days appear below read-only.
 */
export function NursePreferencesPanel({ nurseId, manager = false }: { nurseId: string; manager?: boolean }) {
  const { t } = useLang();
  const { data: pref } = useNursePreferences(nurseId);
  const upsert = useUpsertPreferences();

  const [year] = useState(now.getFullYear());
  const [month] = useState(now.getMonth());
  const { data: monthUnavails = [] } = useNurseUnavailability(manager ? nurseId : undefined, year, month);
  const { data: upcoming = [] } = useUpcomingUnavailability(manager ? undefined : nurseId);
  const addUnavail = useAddUnavailability();
  const removeUnavail = useRemoveUnavailability();

  const { data: myRequests = [] } = useMyDayOffRequests(manager ? undefined : nurseId);
  const addRequest = useAddDayOffRequest();
  const withdraw = useWithdrawDayOffRequest();

  const [newDate, setNewDate] = useState("");
  const [newReason, setNewReason] = useState("");
  const [reqStart, setReqStart] = useState("");
  const [reqEnd, setReqEnd] = useState("");
  const [reqReason, setReqReason] = useState("");
  const [rangeError, setRangeError] = useState("");

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

  const handleSubmitRequest = () => {
    if (!reqStart || !reqEnd) return;
    if (reqEnd < reqStart) {
      setRangeError(t("pref.invalidRange"));
      return;
    }
    setRangeError("");
    addRequest.mutate({ nurse_id: nurseId, start_date: reqStart, end_date: reqEnd, reason: reqReason || undefined });
    setReqStart("");
    setReqEnd("");
    setReqReason("");
  };

  const statusLabel = (s: string) =>
    s === "approved" ? t("req.approved") : s === "denied" ? t("req.denied") : t("req.pendingBadge");

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

      {manager ? (
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
          {monthUnavails.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t("pref.noUnavail")}</p>
          ) : (
            <div className="space-y-1">
              {monthUnavails.map(u => (
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
      ) : (
        <>
          <div>
            <h3 className="text-sm font-semibold mb-1">{t("pref.requestTitle")}</h3>
            <p className="text-xs text-muted-foreground mb-3">{t("pref.requestSub")}</p>
            <div className="flex flex-wrap items-end gap-2 mb-2">
              <div>
                <label className="text-xs text-muted-foreground">{t("pref.from")}</label>
                <input type="date" value={reqStart} onChange={e => setReqStart(e.target.value)}
                  className="block px-3 py-2 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30" />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">{t("pref.to")}</label>
                <input type="date" value={reqEnd} onChange={e => setReqEnd(e.target.value)}
                  className="block px-3 py-2 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30" />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">{t("pref.reason")}</label>
                <input type="text" value={reqReason} onChange={e => setReqReason(e.target.value)} placeholder={t("pref.reasonPh")}
                  className="block px-3 py-2 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30" />
              </div>
              <button onClick={handleSubmitRequest} disabled={!reqStart || !reqEnd || addRequest.isPending}
                className="inline-flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors">
                <Send className="w-4 h-4" /> {t("pref.submitRequest")}
              </button>
            </div>
            {rangeError && <p className="text-xs text-destructive">{rangeError}</p>}
          </div>

          <div>
            <h3 className="text-sm font-semibold mb-3">{t("pref.myRequests")}</h3>
            {myRequests.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t("pref.noRequests")}</p>
            ) : (
              <div className="space-y-1">
                {myRequests.map(r => (
                  <div key={r.id} className="flex items-center gap-3 text-sm py-1.5 px-2 rounded hover:bg-muted/50">
                    <span className="font-medium whitespace-nowrap">{r.start_date} → {r.end_date}</span>
                    <span className="text-muted-foreground truncate">{r.reason || "—"}</span>
                    <span className={`ml-auto inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_BADGE[r.status]}`}>
                      {statusLabel(r.status)}
                    </span>
                    {r.status === "pending" && (
                      <button onClick={() => withdraw.mutate(r.id)}
                        className="text-xs text-muted-foreground hover:text-destructive underline">
                        {t("pref.withdraw")}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <h3 className="text-sm font-semibold mb-3">{t("pref.approvedDates")}</h3>
            {upcoming.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t("pref.noApproved")}</p>
            ) : (
              <div className="space-y-1">
                {upcoming.map((u) => (
                  <div key={u.id} className="flex items-center gap-3 text-sm py-1 px-2 rounded hover:bg-muted/50">
                    <span className="font-medium">{u.date}</span>
                    <span className="text-muted-foreground">{u.reason || "—"}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      <SoftConstraintsPanel nurseId={nurseId} />
    </div>
  );
}
