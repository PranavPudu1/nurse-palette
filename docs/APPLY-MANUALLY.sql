-- Day-off requests: nurses submit a DATE RANGE, managers approve or deny,
-- and the status stays visible to the nurse. Approval materializes per-day
-- rows into nurse_unavailability, so the optimizer path is unchanged:
-- approved = hard constraint, pending/denied = ignored.
CREATE TABLE public.day_off_requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nurse_id uuid NOT NULL REFERENCES public.nurses(id) ON DELETE CASCADE,
  start_date date NOT NULL,
  end_date date NOT NULL,
  reason text,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'denied')),
  decided_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (end_date >= start_date)
);
ALTER TABLE public.day_off_requests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Managers can manage day off requests" ON public.day_off_requests
  FOR ALL USING (is_manager()) WITH CHECK (is_manager());
CREATE POLICY "Nurses can read own requests" ON public.day_off_requests
  FOR SELECT USING (nurse_id IN (SELECT id FROM public.nurses WHERE user_id = auth.uid()));
CREATE POLICY "Nurses can insert own requests" ON public.day_off_requests
  FOR INSERT WITH CHECK (
    nurse_id IN (SELECT id FROM public.nurses WHERE user_id = auth.uid())
    AND status = 'pending'
  );
CREATE POLICY "Nurses can withdraw own pending requests" ON public.day_off_requests
  FOR DELETE USING (
    nurse_id IN (SELECT id FROM public.nurses WHERE user_id = auth.uid())
    AND status = 'pending'
  );

CREATE INDEX idx_day_off_requests_pending ON public.day_off_requests (created_at)
  WHERE status = 'pending';

-- Generated schedule options, saved per run so they survive tab switches
-- and Apply ("can we just save it?" - Sep 16 meeting).
CREATE TABLE public.schedule_generations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  year integer NOT NULL,
  month integer NOT NULL,
  options jsonb NOT NULL,
  created_by uuid,
  created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.schedule_generations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Managers can manage schedule generations" ON public.schedule_generations
  FOR ALL USING (is_manager()) WITH CHECK (is_manager());

CREATE INDEX idx_schedule_generations_month ON public.schedule_generations (year, month, created_at DESC);

-- ============================================================
-- ONLY needed if Lovable's GitHub sync did not apply the migration above
-- automatically: paste this whole file into the Supabase dashboard SQL
-- editor (project cxmjgbahkunsgtvbxhym) and run it once.
-- The edge function change (supabase/functions/generate-schedule/index.ts,
-- the extra_unavailability input used by the what-if preview) also needs a
-- redeploy; Lovable normally does this on sync. If the what-if preview
-- errors, redeploy the function from the Supabase dashboard or Lovable.
-- ============================================================
