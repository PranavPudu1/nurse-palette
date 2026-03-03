import { useState } from "react";
import { useWardConfig, useUpdateWardConfig } from "@/hooks/useWardConfig";
import { Save } from "lucide-react";

const SHIFT_LABELS: Record<string, string> = { D: "Day", E: "Evening", N: "Night" };

export function WardConfigPanel() {
  const { data: configs = [], isLoading } = useWardConfig("General");
  const updateConfig = useUpdateWardConfig();
  const [edits, setEdits] = useState<Record<string, { required_nurses: number; level_mix: Record<string, number> }>>({});

  const getEdit = (id: string, config: { required_nurses: number; level_mix: Record<string, number> }) =>
    edits[id] ?? { required_nurses: config.required_nurses, level_mix: { ...config.level_mix } };

  const setEdit = (id: string, val: { required_nurses: number; level_mix: Record<string, number> }) => {
    setEdits(prev => ({ ...prev, [id]: val }));
  };

  const handleSave = (id: string) => {
    const edit = edits[id];
    if (!edit) return;
    updateConfig.mutate({ id, required_nurses: edit.required_nurses, level_mix: edit.level_mix });
    setEdits(prev => { const n = { ...prev }; delete n[id]; return n; });
  };

  if (isLoading) return <div className="py-8 text-center text-muted-foreground">Loading ward config…</div>;

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Ward Staffing Configuration</h2>
      <p className="text-sm text-muted-foreground">Set required nurses per shift and the seniority level mix.</p>

      <div className="grid gap-4 md:grid-cols-3">
        {configs.map(cfg => {
          const edit = getEdit(cfg.id, cfg);
          const hasChanges = !!edits[cfg.id];

          return (
            <div key={cfg.id} className="rounded-lg border border-border bg-card p-4 space-y-3">
              <h3 className="font-semibold text-sm">{SHIFT_LABELS[cfg.shift_type] ?? cfg.shift_type} Shift ({cfg.shift_type})</h3>

              <div>
                <label className="text-xs text-muted-foreground">Required Nurses</label>
                <input type="number" min={1} max={20} value={edit.required_nurses}
                  onChange={e => setEdit(cfg.id, { ...edit, required_nurses: parseInt(e.target.value) || 1 })}
                  className="block w-full px-3 py-2 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30 mt-1" />
              </div>

              <div>
                <label className="text-xs text-muted-foreground">Level Mix (nurses per level)</label>
                <div className="space-y-1 mt-1">
                  {[1, 2, 3, 4, 5].map(lvl => (
                    <div key={lvl} className="flex items-center gap-2">
                      <span className="text-xs w-14 text-muted-foreground">Level {lvl}:</span>
                      <input type="number" min={0} max={10} value={edit.level_mix[String(lvl)] ?? 0}
                        onChange={e => {
                          const newMix = { ...edit.level_mix, [String(lvl)]: parseInt(e.target.value) || 0 };
                          setEdit(cfg.id, { ...edit, level_mix: newMix });
                        }}
                        className="w-16 px-2 py-1 text-sm rounded border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30" />
                    </div>
                  ))}
                </div>
              </div>

              {hasChanges && (
                <button onClick={() => handleSave(cfg.id)}
                  className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors w-full justify-center">
                  <Save className="w-4 h-4" /> Save
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
