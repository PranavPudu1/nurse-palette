import { AlertCircle, AlertTriangle } from "lucide-react";
import { useLang } from "@/lib/i18n";

/**
 * Key explaining the two severity levels and their icons. Kept in one place so
 * the grid badges (ViolationIndicator) and the issues list (ViolationsPanel)
 * always mean the same thing:
 *   red circle    = Error (hard rule)  — must not be broken
 *   amber triangle = Warning (soft)    — a preference / recommendation
 */
export function ViolationLegend() {
  const { t } = useLang();
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
      <div className="flex items-center gap-1.5">
        <AlertCircle className="w-3.5 h-3.5 text-destructive shrink-0" />
        <span className="text-muted-foreground">
          <span className="font-medium text-foreground">{t("viol.legendError")}</span> {t("viol.legendErrorDesc")}
        </span>
      </div>
      <div className="flex items-center gap-1.5">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
        <span className="text-muted-foreground">
          <span className="font-medium text-foreground">{t("viol.legendWarning")}</span> {t("viol.legendWarningDesc")}
        </span>
      </div>
    </div>
  );
}
