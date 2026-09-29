-- Temp nurses with a duration (Sep 15 meeting).
--
-- "in the add nurse interface, I think there's a simple category of temporary
-- nurse and duration... the optimizer will consider that this person's only
-- here from this date to this date." Until now the app had no way to say a
-- nurse is only schedulable for part of the month; the only workaround was one
-- nurse_unavailability row per excluded day, with nothing recording that it was
-- a contract window rather than a day off.
--
-- The window is deliberately generic rather than temp-only: a permanent nurse
-- joining or leaving mid-month is the same constraint, and it costs nothing.

ALTER TABLE public.nurses
  ADD COLUMN IF NOT EXISTS employment_type text NOT NULL DEFAULT 'permanent',
  ADD COLUMN IF NOT EXISTS available_from  date,
  ADD COLUMN IF NOT EXISTS available_until date;

ALTER TABLE public.nurses DROP CONSTRAINT IF EXISTS nurses_employment_type_check;
ALTER TABLE public.nurses ADD CONSTRAINT nurses_employment_type_check
  CHECK (employment_type IN ('permanent', 'temp'));

-- A temp must have a bounded window; anyone may have one; it must be ordered.
ALTER TABLE public.nurses DROP CONSTRAINT IF EXISTS nurses_availability_window_check;
ALTER TABLE public.nurses ADD CONSTRAINT nurses_availability_window_check CHECK (
  (employment_type <> 'temp' OR (available_from IS NOT NULL AND available_until IS NOT NULL))
  AND (available_from IS NULL OR available_until IS NULL OR available_until >= available_from)
);

COMMENT ON COLUMN public.nurses.employment_type IS
  'permanent | temp. Temps are schedulable only inside [available_from, available_until].';

-- Nurses see who is a temp in the team grid. This is not contact information,
-- which is the reason nurses_public exists, and the alternative is the team
-- grid silently differing depending on who is looking at it.
-- CREATE OR REPLACE VIEW can only append columns, which is all this does.
CREATE OR REPLACE VIEW public.nurses_public
WITH (security_invoker = on) AS
  SELECT id, name, department, user_id, invite_status, employment_type
    FROM public.nurses;

-- CREATE OR REPLACE cannot change a RETURNS TABLE signature, so this drops first.
DROP FUNCTION IF EXISTS public.get_department_nurses();
CREATE FUNCTION public.get_department_nurses()
RETURNS TABLE(id uuid, name text, department text, employment_type text)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT n.id, n.name, n.department, n.employment_type
    FROM public.nurses n
   WHERE n.invite_status = 'accepted'
     AND n.department = (
       SELECT department FROM public.nurses
        WHERE user_id = auth.uid() AND invite_status = 'accepted'
        LIMIT 1
     )
   ORDER BY n.name;
$$;

GRANT EXECUTE ON FUNCTION public.get_department_nurses() TO authenticated;

-- ──────────────────────────────────────────────
-- Applying a temp-variant schedule: promote the solver's placeholder temps into
-- real nurses and write the shifts, in one transaction.
--
-- Variants are explored with synthetic temps that have no database row, so that
-- a discarded exploration cannot leak fake colleagues into the nurses list or
-- into the next real generation. That means Apply has to create the rows, and
-- schedules.nurse_id has a foreign key, so both writes must succeed together or
-- neither should.
-- ──────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.apply_schedule_with_temps(
  p_temps  jsonb,   -- [{placeholder_id, name, level, available_from, available_until, department}]
  p_shifts jsonb    -- [{nurse_id, date, shift_type}]; nurse_id may be a placeholder_id
)
RETURNS jsonb       -- {placeholder_id: real_uuid}
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  t        jsonb;
  new_id   uuid;
  id_map   jsonb := '{}';
  s        jsonb;
  resolved uuid;
BEGIN
  IF NOT public.is_manager() THEN
    RAISE EXCEPTION 'not authorized';
  END IF;

  FOR t IN SELECT * FROM jsonb_array_elements(COALESCE(p_temps, '[]'::jsonb))
  LOOP
    -- invite_status 'accepted' with no email and no user_id: no login is ever
    -- offered, but the optimizer includes them next month, bounded by the
    -- window, so the schedule just applied stays reproducible.
    INSERT INTO public.nurses (name, level, department, employment_type,
                               available_from, available_until, invite_status)
    VALUES (
      COALESCE(t->>'name', 'Temp'),
      COALESCE((t->>'level')::int, 1),
      COALESCE(t->>'department', 'General'),
      'temp',
      (t->>'available_from')::date,
      (t->>'available_until')::date,
      'accepted'
    )
    RETURNING id INTO new_id;

    id_map := id_map || jsonb_build_object(t->>'placeholder_id', new_id);
  END LOOP;

  FOR s IN SELECT * FROM jsonb_array_elements(COALESCE(p_shifts, '[]'::jsonb))
  LOOP
    resolved := COALESCE(
      (id_map->>(s->>'nurse_id'))::uuid,
      (s->>'nurse_id')::uuid
    );

    INSERT INTO public.schedules (nurse_id, date, shift_type)
    VALUES (resolved, (s->>'date')::date, s->>'shift_type')
    ON CONFLICT (nurse_id, date) DO UPDATE SET shift_type = EXCLUDED.shift_type;
  END LOOP;

  RETURN id_map;
END $$;

GRANT EXECUTE ON FUNCTION public.apply_schedule_with_temps(jsonb, jsonb) TO authenticated;
