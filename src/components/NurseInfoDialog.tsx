import { useState, useEffect } from "react";
import { X, User, Star, Moon, Sun, Calendar, AlertTriangle } from "lucide-react";
import { useNursePreferences, useNurseUnavailability } from "@/hooks/useNursePreferences";
import { useSoftConstraints } from "@/hooks/useSoftConstraints";

interface NurseInfo {
  id: string;
  name: string;
  level?: number;
  email?: string | null;
  phone?: string | null;
  department?: string | null;
}

interface Props {
  nurse: NurseInfo | null;
  onClose: () => void;
}

const LEVEL_LABELS: Record<number, string> = {
  1: "Junior",
  2: "Mid-level",
  3: "Senior",
  4: "Specialist",
  5: "Lead",
};

const CONSTRAINT_LABELS: Record<string, string> = {
  soft_unavail: "Soft Unavailability",
  prefer_night: "Prefers Night Shifts",
  avoid_night: "Avoids Night Shifts",
  soft_max_nights: "Night Shift Cap",
  maximize_shifts: "Maximize Shifts",
};

export function NurseInfoDialog({ nurse, onClose }: Props) {
  if (!nurse) return null;

  const now = new Date();
  const { data: pref } = useNursePreferences(nurse.id);
  const { data: unavails = [] } = useNurseUnavailability(nurse.id, now.getFullYear(), now.getMonth());
  const { data: softConstraints = [] } = useSoftConstraints();

  const nurseSoftConstraints = softConstraints.filter((sc) => sc.nurse_id === nurse.id);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="bg-card border border-border rounded-xl shadow-xl w-full max-w-md mx-4 max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <User className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-foreground">{nurse.name}</h2>
              <p className="text-xs text-muted-foreground">{nurse.department ?? "General"}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-md hover:bg-muted transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-5">
          {/* Level */}
          <div className="flex items-center gap-2">
            <Star className="w-4 h-4 text-amber-500" />
            <span className="text-sm font-medium">Level {nurse.level ?? 1}</span>
            <span className="text-xs text-muted-foreground">
              ({LEVEL_LABELS[nurse.level ?? 1] ?? `Level ${nurse.level}`})
            </span>
          </div>

          {/* Contact */}
          {(nurse.email || nurse.phone) && (
            <div className="space-y-1">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Contact</h3>
              {nurse.email && <p className="text-sm">{nurse.email}</p>}
              {nurse.phone && <p className="text-sm">{nurse.phone}</p>}
            </div>
          )}

          {/* Shift Preferences */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Shift Preferences</h3>
            {pref ? (
              <div className="flex flex-wrap gap-2">
                {pref.prefers_weekend && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded-full bg-primary/10 text-primary font-medium">
                    <Calendar className="w-3 h-3" /> Weekend
                  </span>
                )}
                {pref.prefers_weekday && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded-full bg-primary/10 text-primary font-medium">
                    <Sun className="w-3 h-3" /> Weekday
                  </span>
                )}
                {pref.prefers_night && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded-full bg-primary/10 text-primary font-medium">
                    <Moon className="w-3 h-3" /> Night
                  </span>
                )}
                {!pref.prefers_weekend && !pref.prefers_weekday && !pref.prefers_night && (
                  <span className="text-sm text-muted-foreground">No shift preferences set</span>
                )}
                {pref.notes && (
                  <p className="text-xs text-muted-foreground w-full mt-1">Note: {pref.notes}</p>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No preferences set</p>
            )}
          </div>

          {/* Soft Constraints */}
          {nurseSoftConstraints.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Soft Constraints</h3>
              <div className="space-y-1.5">
                {nurseSoftConstraints.map((sc) => {
                  const params = sc.params as Record<string, any>;
                  return (
                    <div key={sc.id} className="flex items-center justify-between text-sm py-1.5 px-3 rounded-md bg-muted/50">
                      <span>{CONSTRAINT_LABELS[sc.constraint_type] ?? sc.constraint_type}</span>
                      <span className="text-xs text-muted-foreground font-medium">
                        weight: {params.weight ?? "—"}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Unavailability */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              Unavailable Dates (this month)
            </h3>
            {unavails.length > 0 ? (
              <div className="space-y-1">
                {unavails.map((u) => (
                  <div key={u.id} className="flex items-center gap-2 text-sm py-1 px-3 rounded-md bg-muted/50">
                    <AlertTriangle className="w-3 h-3 text-amber-500" />
                    <span className="font-medium">{u.date}</span>
                    <span className="text-muted-foreground text-xs">{u.reason || ""}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No unavailable dates this month</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
