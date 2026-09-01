import { useState } from "react";
import { useWardConfig, useUpdateWardConfig } from "@/hooks/useWardConfig";
import { Save } from "lucide-react";
import { useLang } from "@/lib/i18n";

export function WardConfigPanel() {
  const { t } = useLang();
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

  if (isLoading) return <div className="py-8 text-center text-muted-foreground">{t("ward.loading")}</div>;

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">{t("ward.title")}</h2>
      <p className="text-sm text-muted-foreground">{t("ward.subtitle")}</p>

      <div className="grid gap-4 md:grid-cols-3">
        {configs.map(cfg => {
          const edit = getEdit(cfg.id, cfg);
          const hasChanges = !!edits[cfg.id];

          return (
            <div key={cfg.id} className="rounded-lg border border-border bg-card p-4 space-y-3">
              <h3 className="font-semibold text-sm">{t("ward.shiftCard", { shift: t(`shift.${cfg.shift_type}`), code: cfg.shift_type })}</h3>

              <div>
                <label className="text-xs text-muted-foreground">{t("ward.required")}</label>
                <input type="number" min={1} max={20} value={edit.required_nurses}
                  onChange={e => setEdit(cfg.id, { ...edit, required_nurses: parseInt(e.target.value) || 1 })}
                  className="block w-full px-3 py-2 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30 mt-1" />
              </div>

              <div>
                <label className="text-xs text-muted-foreground">{t("ward.levelMix")}</label>
                <div className="space-y-1 mt-1">
                  {[1, 2, 3, 4, 5].map(lvl => (
                    <div key={lvl} className="flex items-center gap-2">
                      <span className="text-xs w-14 text-muted-foreground">{t("ward.levelN", { n: lvl })}</span>
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
                  <Save className="w-4 h-4" /> {t("ward.save")}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
