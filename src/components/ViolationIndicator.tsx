import type { Violation } from "@/lib/schedule-constraints";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { AlertTriangle, AlertCircle } from "lucide-react";
import { useLang } from "@/lib/i18n";

interface Props {
  violations: Violation[];
}

export function ViolationIndicator({ violations }: Props) {
  const { t } = useLang();
  if (violations.length === 0) return null;

  const hasError = violations.some((v) => v.severity === "error");
  const Icon = hasError ? AlertCircle : AlertTriangle;

  return (
    <Tooltip delayDuration={100}>
      <TooltipTrigger asChild>
        <span
          className="absolute -top-1 -right-1 z-30 cursor-help"
          onClick={(e) => e.stopPropagation()}
        >
          <Icon className={`w-3.5 h-3.5 ${hasError ? "text-destructive" : "text-amber-500"}`} />
        </span>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-[250px] z-50">
        <ul className="text-xs space-y-0.5">
          {violations.map((v, i) => (
            <li key={i} className={v.severity === "error" ? "text-destructive" : "text-amber-600"}>
              <span className="font-medium">
                {v.severity === "error" ? t("viol.errorPrefix") : t("viol.warningPrefix")}
              </span>
              {v.message}
            </li>
          ))}
        </ul>
      </TooltipContent>
    </Tooltip>
  );
}
