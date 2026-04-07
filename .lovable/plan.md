

## Plan: Integrate Soft Constraints into the Scheduling System

### Overview
The new optimizer adds a rich soft constraint system on top of the existing hard constraints. This plan covers database, Python API, edge function, and frontend changes needed to support it end-to-end.

### What Changes

**1. New database table: `soft_constraints`**

Stores per-nurse or ward-level soft constraints with type and parameters:

```text
soft_constraints
├── id (uuid, PK)
├── department (text, default 'General')
├── constraint_type (text)  -- e.g. 'soft_unavail', 'prefer_night', 'avoid_night',
│                              'soft_max_nights', 'maximize_shifts', 'level_night_penalty'
├── nurse_id (uuid, nullable) -- null for ward-level constraints like level_night_penalty
├── params (jsonb)  -- flexible: { day: 5, slot: 1, weight: 100 } or { workers: [...], weight: 50 }
│                      or { penalties: { "1": 10, "2": 25, "3": 50 } }
├── created_at (timestamptz)
```

RLS: managers can manage, nurses can read own.

**2. New database table: `scheduling_constraints`**

Stores configurable hard constraint parameters (currently hardcoded):

```text
scheduling_constraints
├── id (uuid, PK)
├── department (text, default 'General', unique)
├── max_shifts_per_day (int, default 1)
├── night_window_max (int, default 1)
├── night_window_k (int, default 3)
├── days_off_after_night_block (int, default 2)
├── max_consecutive_workdays (int, default 4)
├── consec_trigger (int, default 3)
├── days_off_after_consec (int, default 1)
├── updated_at (timestamptz)
```

**3. Update Python API (`python-scheduler/main.py`)**

- Add `SoftConstraintInput` model and `HardConstraintParams` model to the request
- Port the full CP-SAT model from the notebook, including all soft constraint types in the objective function
- Keep the existing multi-solution enumeration via no-good cuts
- Accept configurable hard constraint params instead of hardcoded values

**4. Update Edge Function (`generate-schedule/index.ts`)**

- Fetch `soft_constraints` and `scheduling_constraints` from the database
- Map existing `nurse_preferences` (prefers_weekend, prefers_night, prefers_weekday) into soft constraint format for backward compatibility
- Pass both to the Python API in the payload

**5. Frontend: Soft Constraints Management UI**

- **Ward Config tab**: Add a "Scheduling Rules" section showing the configurable hard constraint parameters (max consecutive days, night window, etc.) with editable inputs
- **Ward Config tab**: Add a "Level Night Penalty" section to set per-level penalties
- **Nurse Preferences panel**: Add ability to create soft constraints per nurse:
  - Soft unavailability with weight (day/slot specific)
  - Prefer/avoid night with weight
  - Soft max nights cap with weight
  - Maximize shifts toggle with weight
- Each soft constraint shows its type, target day/slot, and weight with add/edit/delete

**6. Update `schedule-constraints.ts` (validation)**

- No major changes needed -- the hard constraint validation already covers night-pair, consecutive days, staffing. The soft constraints are optimizer-internal (penalties, not violations).

### File Changes Summary

| File | Change |
|---|---|
| DB migration | Create `soft_constraints` and `scheduling_constraints` tables with RLS |
| `python-scheduler/main.py` | Full rewrite with soft constraint support from notebook |
| `supabase/functions/generate-schedule/index.ts` | Fetch and pass soft constraints + hard constraint config |
| `src/hooks/useSoftConstraints.tsx` | New hook for CRUD on soft_constraints table |
| `src/hooks/useSchedulingConstraints.tsx` | New hook for scheduling_constraints table |
| `src/components/SoftConstraintsPanel.tsx` | New UI for managing per-nurse soft constraints |
| `src/components/SchedulingRulesPanel.tsx` | New UI for hard constraint params + level night penalty |
| `src/components/WardConfigPanel.tsx` | Add links/sections for new panels |
| `src/components/NursePreferencesPanel.tsx` | Integrate soft constraint management per nurse |
| `src/pages/Index.tsx` | Possibly add a new tab or sub-tab for scheduling rules |

### Implementation Order
1. Database migrations (2 tables + RLS)
2. Python API rewrite with soft constraints
3. Edge function update to pass new data
4. Frontend hooks for new tables
5. Frontend UI components
6. End-to-end testing

