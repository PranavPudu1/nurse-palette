import { useState } from "react";
import { useNurseSoftConstraints, useAddSoftConstraint, useRemoveSoftConstraint } from "@/hooks/useSoftConstraints";
import { Trash2, Plus } from "lucide-react";

const CONSTRAINT_TYPES = [
  { value: "soft_unavail", label: "Soft Unavailability", needsDay: true, needsSlot: true },
  { value: "soft_prefer_work", label: "Prefer Working", needsDay: true, needsSlot: true },
  { value: "soft_prefer_shift", label: "Prefer Specific Shift", needsDay: true, needsSlot: true },
  { value: "prefer_night", label: "Prefer Night Shifts", needsDay: false, needsSlot: false },
  { value: "avoid_night", label: "Avoid Night Shifts", needsDay: false, needsSlot: false },
  { value: "soft_max_nights", label: "Soft Max Nights Cap", needsDay: false, needsSlot: false },
  { value: "maximize_shifts", label: "Maximize Shifts", needsDay: false, needsSlot: false },
];

const SLOT_OPTIONS = [
  { value: "", label: "All slots" },
  { value: "1", label: "Day (1)" },
  { value: "2", label: "Evening (2)" },
  { value: "3", label: "Night (3)" },
];

export function SoftConstraintsPanel({ nurseId }: { nurseId: string }) {
  const { data: constraints = [] } = useNurseSoftConstraints(nurseId);
  const addConstraint = useAddSoftConstraint();
  const removeConstraint = useRemoveSoftConstraint();

  const [type, setType] = useState("soft_unavail");
  const [day, setDay] = useState("");
  const [slot, setSlot] = useState("");
  const [weight, setWeight] = useState("50");
  const [maxNights, setMaxNights] = useState("2");

  const selectedType = CONSTRAINT_TYPES.find(t => t.value === type);

  const handleAdd = () => {
    const w = parseInt(weight) || 50;
    const params: Record<string, any> = { weight: w };

    if (selectedType?.needsDay && day) {
      params.day = parseInt(day);
    }
    if (selectedType?.needsSlot && slot) {
      params.slot = parseInt(slot);
    }
    if (type === "soft_max_nights") {
      params.max_nights = parseInt(maxNights) || 2;
    }

    addConstraint.mutate({
      constraint_type: type,
      nurse_id: nurseId,
      params,
    });

    setDay("");
    setSlot("");
  };

  const typeLabel = (ct: string) => CONSTRAINT_TYPES.find(t => t.value === ct)?.label ?? ct;

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold">Soft Constraints</h3>

      {/* Add form */}
      <div className="flex flex-wrap items-end gap-2 p-3 rounded-lg border border-border bg-card">
        <div>
          <label className="text-xs text-muted-foreground">Type</label>
          <select
            value={type}
            onChange={e => setType(e.target.value)}
            className="block px-2 py-1.5 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30"
          >
            {CONSTRAINT_TYPES.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        {selectedType?.needsDay && (
          <div>
            <label className="text-xs text-muted-foreground">Day #</label>
            <input
              type="number"
              min={1}
              max={31}
              value={day}
              onChange={e => setDay(e.target.value)}
              placeholder="1-31"
              className="block w-20 px-2 py-1.5 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30"
            />
          </div>
        )}

        {selectedType?.needsSlot && (
          <div>
            <label className="text-xs text-muted-foreground">Slot</label>
            <select
              value={slot}
              onChange={e => setSlot(e.target.value)}
              className="block px-2 py-1.5 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30"
            >
              {SLOT_OPTIONS.map(s => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
        )}

        {type === "soft_max_nights" && (
          <div>
            <label className="text-xs text-muted-foreground">Max Nights</label>
            <input
              type="number"
              min={0}
              max={15}
              value={maxNights}
              onChange={e => setMaxNights(e.target.value)}
              className="block w-16 px-2 py-1.5 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30"
            />
          </div>
        )}

        <div>
          <label className="text-xs text-muted-foreground">Weight</label>
          <input
            type="number"
            min={1}
            max={500}
            value={weight}
            onChange={e => setWeight(e.target.value)}
            className="block w-20 px-2 py-1.5 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring/30"
          />
        </div>

        <button
          onClick={handleAdd}
          className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-4 h-4" /> Add
        </button>
      </div>

      {/* Existing constraints */}
      {constraints.length === 0 ? (
        <p className="text-sm text-muted-foreground">No soft constraints set.</p>
      ) : (
        <div className="space-y-1">
          {constraints.map(c => (
            <div key={c.id} className="flex items-center gap-3 text-sm py-1.5 px-2 rounded hover:bg-muted/50">
              <span className="font-medium">{typeLabel(c.constraint_type)}</span>
              {c.params.day && <span className="text-muted-foreground">Day {c.params.day}</span>}
              {c.params.slot && <span className="text-muted-foreground">Slot {c.params.slot}</span>}
              {c.params.max_nights != null && <span className="text-muted-foreground">Cap: {c.params.max_nights}</span>}
              <span className="text-muted-foreground">w={c.params.weight}</span>
              <button
                onClick={() => removeConstraint.mutate(c.id)}
                className="ml-auto p-1 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
