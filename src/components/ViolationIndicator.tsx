import type { Violation } from "@/lib/schedule-constraints";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { AlertTriangle, AlertCircle } from "lucide-react";

interface Props {
  violations: Violation[];
}

export function ViolationIndicator({ violations }: Props) {
  if (violations.length === 0) return null;

  const hasError = violations.some((v) => v.severity === "error");
  const Icon = hasError ? AlertCircle : AlertTriangle;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="absolute -top-1 -right-1 z-10">
            <Icon className={`w-3.5 h-3.5 ${hasError ? "text-destructive" : "text-amber-500"}`} />
          </span>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-[250px]">
          <ul className="text-xs space-y-0.5">
            {violations.map((v, i) => (
              <li key={i} className={v.severity === "error" ? "text-destructive" : "text-amber-600"}>
                {v.message}
              </li>
            ))}
          </ul>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
