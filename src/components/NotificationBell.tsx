import { useState } from "react";
import { Bell } from "lucide-react";
import { useMyNotifications, useMarkNotificationsRead } from "@/hooks/useNotifications";
import { useLang } from "@/lib/i18n";

/**
 * How a nurse learns a decision was made.
 *
 * The manager's final decision writes a notification row; this reads it. Each
 * row stores an i18n key and a payload rather than a finished sentence, so the
 * message renders in whichever language the nurse is using.
 */
export function NotificationBell({ nurseId }: { nurseId?: string }) {
  const { t } = useLang();
  const [open, setOpen] = useState(false);
  const { data: notifications = [] } = useMyNotifications(nurseId);
  const markRead = useMarkNotificationsRead();

  const unread = notifications.filter((n) => !n.read_at);

  const toggle = () => {
    const next = !open;
    setOpen(next);
    if (next && unread.length > 0) markRead.mutate(unread.map((n) => n.id));
  };

  return (
    <div className="relative">
      <button
        onClick={toggle}
        aria-label={t("notif.title")}
        className="relative inline-flex items-center justify-center w-9 h-9 rounded-md bg-secondary text-secondary-foreground hover:bg-accent transition-colors"
      >
        <Bell className="w-4 h-4" />
        {unread.length > 0 && (
          <span className="absolute -top-1 -right-1 min-w-[1rem] h-4 px-1 rounded-full bg-destructive text-destructive-foreground text-[10px] font-bold flex items-center justify-center">
            {unread.length}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 mt-2 w-80 z-50 rounded-lg border border-border bg-card shadow-lg p-2">
            <div className="px-2 py-1 text-sm font-semibold">{t("notif.title")}</div>
            {notifications.length === 0 ? (
              <p className="px-2 py-3 text-sm text-muted-foreground">{t("notif.none")}</p>
            ) : (
              <ul className="max-h-80 overflow-auto">
                {notifications.map((n) => (
                  <li
                    key={n.id}
                    className={`px-2 py-2 rounded text-sm ${n.read_at ? "text-muted-foreground" : "bg-muted/60"}`}
                  >
                    <div>{t(n.body_key, n.payload ?? {})}</div>
                    {n.payload?.note && (
                      <div className="text-xs text-muted-foreground mt-0.5">{String(n.payload.note)}</div>
                    )}
                    <div className="text-xs text-muted-foreground/70 mt-0.5">
                      {n.created_at.slice(0, 10)}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  );
}
