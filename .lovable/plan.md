

## Plan: Seed Demo Data with Soft Constraints & Preferences

### What
Enhance the `demo-login` edge function to also seed nurse preferences, unavailability dates, and soft constraints so evaluators immediately see meaningful data in the Nurse Preferences panel.

### What gets seeded

**Nurse Preferences** (`nurse_preferences` table):
- Demo Nurse: prefers weekday, prefers night
- Sarah Johnson: prefers weekend
- Emily Davis: prefers weekday

**Unavailability** (`nurse_unavailability` table):
- Demo Nurse: 2 dates this month (e.g., "vacation", "appointment")
- Sarah Johnson: 1 date

**Soft Constraints** (`soft_constraints` table):
- Demo Nurse: `avoid_night` (weight 80)
- Sarah Johnson: `soft_unavail` on day 15, slot 1 (weight 60)
- Emily Davis: `prefer_night` (weight 70), `soft_max_nights` cap 3 (weight 50)
- Ward-level: `level_night_penalty` (weight 40, no nurse_id)

### Technical Details

**File changed**: `supabase/functions/demo-login/index.ts`

Add a `seedPreferencesAndConstraints` function called after `seedDemoData`, inside the `if (count <= 1)` block. It will:

1. Upsert into `nurse_preferences` for 3 nurses with varied boolean combos
2. Insert 3 rows into `nurse_unavailability` with dates in the current month
3. Insert 5 rows into `soft_constraints` — 4 per-nurse + 1 ward-level

All inserts use the already-available `nurseId` and `extras` nurse IDs. The function uses `upsert` / `onConflict` where possible to be idempotent on re-runs.

