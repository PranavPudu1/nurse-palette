-- Two-stage time-off decisions (Sep 15 meeting).
--
-- The requests page used to commit the real outcome the moment a manager
-- clicked Approve, so there was no way to ask "what would the schedule look
-- like if I approved this?" without actually approving it. Min's ask: approve
-- and deny on the requests page become exploration, and a separate, explicit
-- final decision is what commits the outcome and notifies the nurse.
--
-- `tentative` is a SEPARATE column rather than a new `status` value on purpose.
-- The nurse UI indexes a badge map by `status` directly, so a new status value
-- would surface a manager's exploration to the nurse as though it were a
-- decision. `status` keeps meaning "committed outcome" and stays 'pending'
-- until the final decision, so a lean can never be mistaken for an outcome.
--
-- Note on visibility: RLS here is row-level, and "Nurses can read own requests"
-- returns the whole row, so a nurse querying the API directly could read
-- `tentative` on their own request. The nurse-facing query selects explicit
-- columns and omits it, and nothing renders it, but this is not enforced by the
-- database. Managers and nurses share the `authenticated` role, so column
-- privileges cannot separate them; hiding it properly would mean moving the
-- nurse read behind a view. Worth doing if a manager's draft lean is considered
-- sensitive.

ALTER TABLE public.day_off_requests
  ADD COLUMN IF NOT EXISTS tentative     text,
  ADD COLUMN IF NOT EXISTS tentative_at  timestamptz,
  ADD COLUMN IF NOT EXISTS decided_by    uuid,
  ADD COLUMN IF NOT EXISTS decision_note text;

ALTER TABLE public.day_off_requests DROP CONSTRAINT IF EXISTS day_off_requests_tentative_check;
ALTER TABLE public.day_off_requests ADD CONSTRAINT day_off_requests_tentative_check
  CHECK (tentative IS NULL OR tentative IN ('approve', 'deny'));

-- Provenance for materialized days off, so reverting a decision can delete
-- exactly the rows that decision created and leave rows a manager or nurse
-- entered by hand alone. Without this, approve-then-deny left a nurse
-- permanently unavailable.
ALTER TABLE public.nurse_unavailability
  ADD COLUMN IF NOT EXISTS request_id uuid REFERENCES public.day_off_requests(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_nurse_unavail_request ON public.nurse_unavailability (request_id);

-- Which requests a saved generation assumed approved, so a past run can never
-- be mistaken for "the schedule under no assumptions".
ALTER TABLE public.schedule_generations
  ADD COLUMN IF NOT EXISTS assumptions jsonb NOT NULL DEFAULT '{}';

-- Notifications. Stores an i18n KEY plus a payload, never a finished sentence:
-- the app is bilingual and translation happens client-side.
CREATE TABLE IF NOT EXISTS public.notifications (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nurse_id   uuid NOT NULL REFERENCES public.nurses(id) ON DELETE CASCADE,
  kind       text NOT NULL,
  request_id uuid REFERENCES public.day_off_requests(id) ON DELETE CASCADE,
  body_key   text NOT NULL,
  payload    jsonb NOT NULL DEFAULT '{}',
  read_at    timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.notifications DROP CONSTRAINT IF EXISTS notifications_kind_check;
ALTER TABLE public.notifications ADD CONSTRAINT notifications_kind_check
  CHECK (kind IN ('day_off_approved', 'day_off_denied', 'day_off_reopened'));

-- Explicit grants: tables created by raw migration in this project do not
-- inherit default privileges and are unreachable without these.
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.notifications TO authenticated;
GRANT ALL ON TABLE public.notifications TO service_role;

ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Managers can manage notifications" ON public.notifications;
CREATE POLICY "Managers can manage notifications" ON public.notifications
  FOR ALL USING (public.is_manager()) WITH CHECK (public.is_manager());

DROP POLICY IF EXISTS "Nurses can read own notifications" ON public.notifications;
CREATE POLICY "Nurses can read own notifications" ON public.notifications
  FOR SELECT USING (
    nurse_id IN (SELECT id FROM public.nurses WHERE user_id = auth.uid())
  );

DROP POLICY IF EXISTS "Nurses can mark own notifications read" ON public.notifications;
CREATE POLICY "Nurses can mark own notifications read" ON public.notifications
  FOR UPDATE USING (
    nurse_id IN (SELECT id FROM public.nurses WHERE user_id = auth.uid())
  );

CREATE INDEX IF NOT EXISTS idx_notifications_unread
  ON public.notifications (nurse_id, created_at DESC) WHERE read_at IS NULL;

-- ──────────────────────────────────────────────
-- Commit: one transaction, so a batch of decisions is all-or-nothing.
-- ──────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.commit_tentative_decisions(p_request_ids uuid[])
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  r public.day_off_requests;
  n integer := 0;
BEGIN
  IF NOT public.is_manager() THEN
    RAISE EXCEPTION 'not authorized';
  END IF;

  FOR r IN
    SELECT * FROM public.day_off_requests
     WHERE id = ANY(p_request_ids) AND tentative IS NOT NULL
     ORDER BY created_at
     FOR UPDATE
  LOOP
    IF r.tentative = 'approve' THEN
      -- Dates expand server-side: exact, no client cap, no timezone hazard.
      -- DO NOTHING so a pre-existing manual row keeps its NULL request_id and
      -- therefore survives a later revert.
      INSERT INTO public.nurse_unavailability (nurse_id, date, reason, request_id)
      SELECT r.nurse_id, d::date, COALESCE(r.reason, 'approved day off'), r.id
        FROM generate_series(r.start_date::timestamp, r.end_date::timestamp, interval '1 day') AS d
      ON CONFLICT (nurse_id, date) DO NOTHING;
    ELSE
      DELETE FROM public.nurse_unavailability WHERE request_id = r.id;
    END IF;

    UPDATE public.day_off_requests
       SET status     = CASE WHEN r.tentative = 'approve' THEN 'approved' ELSE 'denied' END,
           decided_at = now(),
           decided_by = auth.uid(),
           tentative  = NULL
     WHERE id = r.id;

    INSERT INTO public.notifications (nurse_id, kind, request_id, body_key, payload)
    VALUES (
      r.nurse_id,
      CASE WHEN r.tentative = 'approve' THEN 'day_off_approved' ELSE 'day_off_denied' END,
      r.id,
      CASE WHEN r.tentative = 'approve' THEN 'notif.dayOffApproved' ELSE 'notif.dayOffDenied' END,
      jsonb_build_object('start', r.start_date, 'end', r.end_date, 'note', r.decision_note)
    );

    n := n + 1;
  END LOOP;

  RETURN n;
END $$;

-- ──────────────────────────────────────────────
-- Revert: undo a committed decision and clean up exactly its own rows.
-- ──────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.revert_day_off_decision(p_request_id uuid)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  r public.day_off_requests;
BEGIN
  IF NOT public.is_manager() THEN
    RAISE EXCEPTION 'not authorized';
  END IF;

  SELECT * INTO r FROM public.day_off_requests WHERE id = p_request_id FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'request not found';
  END IF;

  DELETE FROM public.nurse_unavailability WHERE request_id = p_request_id;

  UPDATE public.day_off_requests
     SET status = 'pending', decided_at = NULL, decided_by = NULL, tentative = NULL
   WHERE id = p_request_id;

  INSERT INTO public.notifications (nurse_id, kind, request_id, body_key, payload)
  VALUES (r.nurse_id, 'day_off_reopened', r.id, 'notif.dayOffReopened',
          jsonb_build_object('start', r.start_date, 'end', r.end_date));
END $$;

GRANT EXECUTE ON FUNCTION public.commit_tentative_decisions(uuid[]) TO authenticated;
GRANT EXECUTE ON FUNCTION public.revert_day_off_decision(uuid) TO authenticated;
