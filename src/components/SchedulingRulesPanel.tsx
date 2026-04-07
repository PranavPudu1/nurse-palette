import { useState, useEffect } from "react";
import { useSchedulingConstraints, useUpdateSchedulingConstraints } from "@/hooks/useSchedulingConstraints";
import { useSoftConstraints, useAddSoftConstraint, useRemoveSoftConstraint } from "@/hooks/useSoftConstraints";
import { Save, Trash2, Plus } from "lucide-react";

const RULE_FIELDS = [
  { key: "max_shifts_per_day", label: "Max shifts per nurse per day", min: 1, max: 3 },
  { key: "night_window_max", label: "Max night shifts in sliding window", min: 1, max: 5 },
  { key: "night_window_k", label: "Night sliding window size (days)", min: 2, max: 7 },
  { key: "days_off_after_night_block", label: "Days off after consecutive nights", min: 0, max: 5 },
  { key: "max_consecutive_workdays", label: "Max consecutive workdays", min: 2, max: 7 },
  { key: "consec_trigger", label: "Consecutive days trigger for rest", min: 2, max: 7 },
  { key: "days_off_after_consec", label: "Days off after consecutive trigger", min: 0, max: 5 },
] as const;

export function SchedulingRulesPanel() {
  const { data: config, isLoading } = useSchedulingConstraints("General");
  const updateConfig = useUpdateSchedulingConstraints();
  const { data: softCons = [] } = useSoftConstraints("General");
  const addSoft = useAddSoftConstraint();
  const removeSoft = useRemoveSoftConstraint();

  const [edits, setEdits] = useState<Record<string, number>>({});
  const [hasChanges, setHasChanges] = useState(false);

  // Level night penalty state
  const [penalties, setPenalties] = useState<Record<string, number>>({ "1": 0, "2": 0, "3": 0, "4": 0, "5": 0 });
  const existingLevelPenalty = softCons.find(sc => sc.constraint_type === "level_night_penalty");

  useEffect(() => {
    if (existingLevelPenalty) {
      setPenalties({ "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, ...existingLevelPenalty.params.penalties });
    }
  }, [existingLevelPenalty]);

  useEffect(() => {
    if (config) {
      const e: Record<string, number> = {};
      for (const f of RULE_FIELDS) {
        e[f.key] = (config as any)[f.key];
      }
      setEdits(e);
      setHasChanges(false);
    }
  }, [config]);

  const handleFieldChange = (key: string, val: number) => {
    setEdits(prev => ({ ...prev, [key]: val }));
    setHasChanges(true);
  };

  const handleSaveRules = () => {
    if (!config) return;
    updateConfig.mutate({ id: config.id, ...edits } as any);
    setHasChanges(false);
  };

  const handleSaveLevelPenalty = () => {
    if (existingLevelPenalty) {
      removeSoft.mutate(existingLevelPenalty.id);
    }
    // Small delay to avoid race
    setTimeout(() => {
      addSoft.mutate({
        constraint_type: "level_night_penalty",
        params: { penalties },
      });
    }, 200);
  };

  if (isLoading) return <div className="py-8 text-center text-muted-foreground">Loading…</div>;

  return (
    <div className="space-y-8">
      {/* Hard Constraint Rules */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Scheduling Rules</h2>
        <p className="text-sm text-muted-foreground">
          Configure the hard constraint parameters used by the optimizer.
        </p>

        <div className="grid gap-3 md:grid-cols-2">
          {RULE_FIELDS.map(f => (
            <div key={f.key} className="flex items-center gap-3 rounded-lg border border-border bg-card p-3">
              <label className="flex-1 text-sm">{f.label}</label>
              <input
                type="number"
                min={f.min}
                max={f.max}
                value={edits[f.key] ?? 0}
                onChange={e => handleFieldChange(f.key, parseInt(e.target.value) || f.min)}
                className="w-16 px-2 py-1.5 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30 text-center"
              />
            </div>
          ))}
        </div>

        {hasChanges && (
          <button
            onClick={handleSaveRules}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Save className="w-4 h-4" /> Save Rules
          </button>
        )}
      </div>

      {/* Level Night Penalty */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Level-Based Night Penalty</h2>
        <p className="text-sm text-muted-foreground">
          Set penalty weights per nurse level for night shift assignments. Higher = stronger aversion.
        </p>

        <div className="grid gap-2 md:grid-cols-5">
          {[1, 2, 3, 4, 5].map(lvl => (
            <div key={lvl} className="flex items-center gap-2 rounded-lg border border-border bg-card p-3">
              <span className="text-sm font-medium">Level {lvl}</span>
              <input
                type="number"
                min={0}
                max={200}
                value={penalties[String(lvl)] ?? 0}
                onChange={e => setPenalties(prev => ({ ...prev, [String(lvl)]: parseInt(e.target.value) || 0 }))}
                className="w-16 px-2 py-1.5 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30 text-center"
              />
            </div>
          ))}
        </div>

        <button
          onClick={handleSaveLevelPenalty}
          className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Save className="w-4 h-4" /> Save Level Penalties
        </button>
      </div>
    </div>
  );
}
