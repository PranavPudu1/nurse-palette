import { useState } from "react";
import { useNurses, useAddNurse, useRemoveNurse, useUpdateNurse, DbNurse } from "@/hooks/useNurses";
import { Plus, Trash2, Pencil, X, Check, User } from "lucide-react";
import { useLang } from "@/lib/i18n";

export function NursesPanel() {
  const { t } = useLang();
  const { data: nurses = [], isLoading } = useNurses();
  const addNurse = useAddNurse();
  const removeNurse = useRemoveNurse();
  const updateNurse = useUpdateNurse();

  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", phone: "", department: "General", level: "1" });
  const [editId, setEditId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({ name: "", email: "", phone: "", department: "", level: "1" });

  const handleAdd = () => {
    if (!form.name.trim()) return;
    addNurse.mutate({
      name: form.name,
      email: form.email || undefined,
      phone: form.phone || undefined,
      department: form.department || "General",
      level: parseInt(form.level) || 1,
    });
    setForm({ name: "", email: "", phone: "", department: "General", level: "1" });
    setShowAdd(false);
  };

  const startEdit = (n: DbNurse) => {
    setEditId(n.id);
    setEditForm({
      name: n.name,
      email: n.email || "",
      phone: n.phone || "",
      department: n.department || "",
      level: String(n.level ?? 1),
    });
  };

  const saveEdit = () => {
    if (!editId || !editForm.name.trim()) return;
    updateNurse.mutate({ id: editId, name: editForm.name, email: editForm.email, phone: editForm.phone, department: editForm.department, level: parseInt(editForm.level) || 1 });
    setEditId(null);
  };

  if (isLoading) return <div className="py-12 text-center text-muted-foreground">{t("nurses.loading")}</div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{t("nurses.title", { n: nurses.length })}</h2>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-4 h-4" /> {t("grid.addNurse")}
        </button>
      </div>

      {showAdd && (
        <div className="rounded-lg border border-border bg-card p-4 space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <input placeholder={t("nurses.nameReq")} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="px-3 py-2 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30" />
            <input placeholder={t("nurses.email")} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="px-3 py-2 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30" />
            <input placeholder={t("nurses.phone")} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })}
              className="px-3 py-2 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30" />
            <input placeholder={t("nurses.dept")} value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })}
              className="px-3 py-2 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30" />
            <div className="flex items-center gap-2">
              <label className="text-sm text-muted-foreground whitespace-nowrap">{t("nurses.level")}</label>
              <select value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })}
                className="px-3 py-2 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30 w-full">
                {[1,2,3,4,5].map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={handleAdd} disabled={!form.name.trim() || addNurse.isPending}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors">
              <Check className="w-4 h-4" /> {t("nurses.save")}
            </button>
            <button onClick={() => setShowAdd(false)}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-secondary text-secondary-foreground hover:bg-accent transition-colors">
              <X className="w-4 h-4" /> {t("nurses.cancel")}
            </button>
          </div>
        </div>
      )}

      <div className="rounded-lg border border-border bg-card overflow-hidden">
        {nurses.length === 0 ? (
          <div className="py-12 text-center text-muted-foreground">{t("nurses.none")}</div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground uppercase">{t("nurses.name")}</th>
                <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground uppercase w-16">{t("nurses.lvl")}</th>
                <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground uppercase hidden sm:table-cell">{t("nurses.email")}</th>
                <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground uppercase hidden md:table-cell">{t("nurses.deptShort")}</th>
                <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground uppercase hidden sm:table-cell">{t("nurses.status")}</th>
                <th className="px-4 py-2.5 w-24" />
              </tr>
            </thead>
            <tbody>
              {nurses.map((n) => (
                <tr key={n.id} className="border-b border-border last:border-0 hover:bg-muted/30">
                  {editId === n.id ? (
                    <>
                      <td className="px-4 py-2"><input value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} className="px-2 py-1 text-sm rounded border border-input bg-background w-full" /></td>
                      <td className="px-4 py-2">
                        <select value={editForm.level} onChange={(e) => setEditForm({ ...editForm, level: e.target.value })} className="px-2 py-1 text-sm rounded border border-input bg-background w-full">
                          {[1,2,3,4,5].map(l => <option key={l} value={l}>{l}</option>)}
                        </select>
                      </td>
                      <td className="px-4 py-2 hidden sm:table-cell"><input value={editForm.email} onChange={(e) => setEditForm({ ...editForm, email: e.target.value })} className="px-2 py-1 text-sm rounded border border-input bg-background w-full" /></td>
                      <td className="px-4 py-2 hidden md:table-cell"><input value={editForm.department} onChange={(e) => setEditForm({ ...editForm, department: e.target.value })} className="px-2 py-1 text-sm rounded border border-input bg-background w-full" /></td>
                      <td className="hidden sm:table-cell" />
                      <td className="px-4 py-2 flex gap-1">
                        <button onClick={saveEdit} className="p-1.5 rounded hover:bg-primary/10 text-primary"><Check className="w-4 h-4" /></button>
                        <button onClick={() => setEditId(null)} className="p-1.5 rounded hover:bg-muted text-muted-foreground"><X className="w-4 h-4" /></button>
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="px-4 py-2.5 text-sm font-medium flex items-center gap-2"><User className="w-4 h-4 text-muted-foreground" />{n.name}</td>
                      <td className="px-4 py-2.5 text-sm">
                        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-semibold">{n.level}</span>
                      </td>
                      <td className="px-4 py-2.5 text-sm text-muted-foreground hidden sm:table-cell">{n.email || "—"}</td>
                      <td className="px-4 py-2.5 text-sm text-muted-foreground hidden md:table-cell">{n.department || "—"}</td>
                      <td className="px-4 py-2.5 hidden sm:table-cell">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          n.invite_status === "accepted"
                            ? "bg-green-100 text-green-700"
                            : "bg-amber-100 text-amber-700"
                        }`}>
                          {n.invite_status === "accepted" ? t("nurses.active") : t("nurses.pending")}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 flex gap-1">
                        <button onClick={() => startEdit(n)} className="p-1.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"><Pencil className="w-4 h-4" /></button>
                        <button onClick={() => { if (confirm(t("nurses.confirmRemove", { name: n.name }))) removeNurse.mutate(n.id); }} className="p-1.5 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"><Trash2 className="w-4 h-4" /></button>
                      </td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
