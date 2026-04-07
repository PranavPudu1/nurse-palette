import { useState } from "react";
import { AlertTriangle, ChevronRight, ChevronDown, XCircle, AlertCircle } from "lucide-react";
import type { Violation } from "@/lib/schedule-constraints";

interface Props {
  violations: Violation[];
  nurseNames: Record<string, string>;
}

export function ViolationsPanel({ violations, nurseNames }: Props) {
  const [expanded, setExpanded] = useState(true);
  const [filter, setFilter] = useState<"all" | "error" | "warning">("all");

  const filtered = filter === "all" ? violations : violations.filter((v) => v.severity === filter);
  const errors = violations.filter((v) => v.severity === "error");
  const warnings = violations.filter((v) => v.severity === "warning");

  if (violations.length === 0) return null;

  return (
    <div className="border border-border rounded-lg bg-card overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-4 py-3 text-sm font-semibold bg-muted/50 hover:bg-muted transition-colors"
      >
        {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        <AlertTriangle className="w-4 h-4 text-amber-600" />
        <span>
          Schedule Issues
        </span>
        <span className="ml-auto flex items-center gap-2 text-xs font-normal">
          {errors.length > 0 && (
            <span className="text-destructive font-medium">{errors.length} errors</span>
          )}
          {warnings.length > 0 && (
            <span className="text-amber-600 font-medium">{warnings.length} warnings</span>
          )}
        </span>
      </button>

      {expanded && (
        <div>
          <div className="flex gap-1 px-3 py-2 border-b border-border bg-muted/30">
            {(["all", "error", "warning"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                  filter === f
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent"
                }`}
              >
                {f === "all" ? `All (${violations.length})` : f === "error" ? `Errors (${errors.length})` : `Warnings (${warnings.length})`}
              </button>
            ))}
          </div>

          <div className="max-h-[400px] overflow-y-auto divide-y divide-border">
            {filtered.length === 0 ? (
              <div className="px-4 py-6 text-center text-sm text-muted-foreground">
                No {filter === "all" ? "issues" : filter + "s"} found
              </div>
            ) : (
              filtered.map((v, i) => (
                <div key={i} className="flex items-start gap-2.5 px-4 py-2.5 text-sm hover:bg-muted/30 transition-colors">
                  {v.severity === "error" ? (
                    <XCircle className="w-4 h-4 text-destructive shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                  )}
                  <div className="min-w-0">
                    <div className="font-medium text-foreground">
                      {v.nurseId === "__staffing__" ? "Staffing Gap" : (nurseNames[v.nurseId] || v.nurseId.slice(0, 8))}
                    </div>
                    <div className="text-muted-foreground text-xs mt-0.5">
                      {v.message}
                    </div>
                    <div className="text-muted-foreground/60 text-[10px] mt-0.5">
                      {v.date} · {v.rule}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
