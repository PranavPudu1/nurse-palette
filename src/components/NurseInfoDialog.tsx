import { X, User, Star } from "lucide-react";
import { NursePreferencesPanel } from "@/components/NursePreferencesPanel";
import { useLang } from "@/lib/i18n";

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

export function NurseInfoDialog({ nurse, onClose }: Props) {
  const { t } = useLang();
  if (!nurse) return null;

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
            <span className="text-sm font-medium">{t("info.levelN", { n: nurse.level ?? 1 })}</span>
            <span className="text-xs text-muted-foreground">
              ({t(`info.level.${nurse.level ?? 1}`)})
            </span>
          </div>

          {/* Contact */}
          {(nurse.email || nurse.phone) && (
            <div className="space-y-1">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">{t("info.contact")}</h3>
              {nurse.email && <p className="text-sm">{nurse.email}</p>}
              {nurse.phone && <p className="text-sm">{nurse.phone}</p>}
            </div>
          )}

          {/* Editable Preferences, Unavailability & Soft Constraints */}
          <NursePreferencesPanel nurseId={nurse.id} />
        </div>
      </div>
    </div>
  );
}
