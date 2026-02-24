import { useState } from "react";
import { useNurses, useAddNurse, useRemoveNurse, useUpdateNurse, DbNurse } from "@/hooks/useNurses";
import { Plus, Trash2, Pencil, X, Check, User } from "lucide-react";
import { toast } from "sonner";

export function NursesPanel() {
  const { data: nurses = [], isLoading } = useNurses();
  const addNurse = useAddNurse();
  const removeNurse = useRemoveNurse();
  const updateNurse = useUpdateNurse();

  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", phone: "", department: "General" });
  const [editId, setEditId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({ name: "", email: "", phone: "", department: "" });

  const handleAdd = () => {
    if (!form.name.trim()) return;
    addNurse.mutate({ name: form.name, email: form.email || undefined, phone: form.phone || undefined, department: form.department || "General" });
    setForm({ name: "", email: "", phone: "", department: "General" });
    setShowAdd(false);
  };

  const startEdit = (n: DbNurse) => {
    setEditId(n.id);
    setEditForm({ name: n.name, email: n.email || "", phone: n.phone || "", department: n.department || "" });
  };

  const saveEdit = () => {
    if (!editId || !editForm.name.trim()) return;
    updateNurse.mutate({ id: editId, ...editForm });
    setEditId(null);
  };

  if (isLoading) return <div className="py-12 text-center text-muted-foreground">Loading nurses…</div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Nurses ({nurses.length})</h2>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-4 h-4" /> Add Nurse
        </button>
      </div>

      {showAdd && (
        <div className="rounded-lg border border-border bg-card p-4 space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <input placeholder="Name *" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="px-3 py-2 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30" />
            <input placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="px-3 py-2 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30" />
            <input placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })}
              className="px-3 py-2 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30" />
            <input placeholder="Department" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })}
              className="px-3 py-2 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30" />
          </div>
          <div className="flex gap-2">
            <button onClick={handleAdd} disabled={!form.name.trim() || addNurse.isPending}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors">
              <Check className="w-4 h-4" /> Save
            </button>
            <button onClick={() => setShowAdd(false)}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-secondary text-secondary-foreground hover:bg-accent transition-colors">
              <X className="w-4 h-4" /> Cancel
            </button>
          </div>
        </div>
      )}

      <div className="rounded-lg border border-border bg-card overflow-hidden">
        {nurses.length === 0 ? (
          <div className="py-12 text-center text-muted-foreground">No nurses yet. Add one above.</div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground uppercase">Name</th>
                <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground uppercase hidden sm:table-cell">Email</th>
                <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground uppercase hidden md:table-cell">Phone</th>
                <th className="px-4 py-2.5 text-left text-xs font-semibold text-muted-foreground uppercase hidden md:table-cell">Dept</th>
                <th className="px-4 py-2.5 w-24" />
              </tr>
            </thead>
            <tbody>
              {nurses.map((n) => (
                <tr key={n.id} className="border-b border-border last:border-0 hover:bg-muted/30">
                  {editId === n.id ? (
                    <>
                      <td className="px-4 py-2"><input value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} className="px-2 py-1 text-sm rounded border border-input bg-background w-full" /></td>
                      <td className="px-4 py-2 hidden sm:table-cell"><input value={editForm.email} onChange={(e) => setEditForm({ ...editForm, email: e.target.value })} className="px-2 py-1 text-sm rounded border border-input bg-background w-full" /></td>
                      <td className="px-4 py-2 hidden md:table-cell"><input value={editForm.phone} onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })} className="px-2 py-1 text-sm rounded border border-input bg-background w-full" /></td>
                      <td className="px-4 py-2 hidden md:table-cell"><input value={editForm.department} onChange={(e) => setEditForm({ ...editForm, department: e.target.value })} className="px-2 py-1 text-sm rounded border border-input bg-background w-full" /></td>
                      <td className="px-4 py-2 flex gap-1">
                        <button onClick={saveEdit} className="p-1.5 rounded hover:bg-primary/10 text-primary"><Check className="w-4 h-4" /></button>
                        <button onClick={() => setEditId(null)} className="p-1.5 rounded hover:bg-muted text-muted-foreground"><X className="w-4 h-4" /></button>
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="px-4 py-2.5 text-sm font-medium flex items-center gap-2"><User className="w-4 h-4 text-muted-foreground" />{n.name}</td>
                      <td className="px-4 py-2.5 text-sm text-muted-foreground hidden sm:table-cell">{n.email || "—"}</td>
                      <td className="px-4 py-2.5 text-sm text-muted-foreground hidden md:table-cell">{n.phone || "—"}</td>
                      <td className="px-4 py-2.5 text-sm text-muted-foreground hidden md:table-cell">{n.department || "—"}</td>
                      <td className="px-4 py-2.5 flex gap-1">
                        <button onClick={() => startEdit(n)} className="p-1.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"><Pencil className="w-4 h-4" /></button>
                        <button onClick={() => { if (confirm(`Remove ${n.name}?`)) removeNurse.mutate(n.id); }} className="p-1.5 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"><Trash2 className="w-4 h-4" /></button>
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
