
-- 1. Add level (seniority) to nurses
ALTER TABLE public.nurses ADD COLUMN IF NOT EXISTS level integer NOT NULL DEFAULT 1;
COMMENT ON COLUMN public.nurses.level IS 'Seniority level (1=junior, higher=senior)';

-- 2. Nurse preferences
CREATE TABLE public.nurse_preferences (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nurse_id uuid NOT NULL REFERENCES public.nurses(id) ON DELETE CASCADE UNIQUE,
  prefers_weekend boolean NOT NULL DEFAULT false,
  prefers_night boolean NOT NULL DEFAULT false,
  prefers_weekday boolean NOT NULL DEFAULT false,
  notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.nurse_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Managers can manage preferences" ON public.nurse_preferences FOR ALL USING (is_manager()) WITH CHECK (is_manager());
CREATE POLICY "Nurses can read own preferences" ON public.nurse_preferences FOR SELECT USING (nurse_id IN (SELECT id FROM public.nurses WHERE user_id = auth.uid()));
CREATE POLICY "Nurses can update own preferences" ON public.nurse_preferences FOR UPDATE USING (nurse_id IN (SELECT id FROM public.nurses WHERE user_id = auth.uid())) WITH CHECK (nurse_id IN (SELECT id FROM public.nurses WHERE user_id = auth.uid()));
CREATE POLICY "Nurses can insert own preferences" ON public.nurse_preferences FOR INSERT WITH CHECK (nurse_id IN (SELECT id FROM public.nurses WHERE user_id = auth.uid()));

CREATE TRIGGER update_nurse_preferences_updated_at BEFORE UPDATE ON public.nurse_preferences FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- 3. Nurse unavailability
CREATE TABLE public.nurse_unavailability (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nurse_id uuid NOT NULL REFERENCES public.nurses(id) ON DELETE CASCADE,
  date date NOT NULL,
  reason text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(nurse_id, date)
);
ALTER TABLE public.nurse_unavailability ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Managers can manage unavailability" ON public.nurse_unavailability FOR ALL USING (is_manager()) WITH CHECK (is_manager());
CREATE POLICY "Nurses can read own unavailability" ON public.nurse_unavailability FOR SELECT USING (nurse_id IN (SELECT id FROM public.nurses WHERE user_id = auth.uid()));
CREATE POLICY "Nurses can insert own unavailability" ON public.nurse_unavailability FOR INSERT WITH CHECK (nurse_id IN (SELECT id FROM public.nurses WHERE user_id = auth.uid()));
CREATE POLICY "Nurses can delete own unavailability" ON public.nurse_unavailability FOR DELETE USING (nurse_id IN (SELECT id FROM public.nurses WHERE user_id = auth.uid()));

-- 4. Ward shift configuration (per-shift staffing needs)
CREATE TABLE public.ward_shift_config (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  department text NOT NULL DEFAULT 'General',
  shift_type text NOT NULL CHECK (shift_type IN ('D', 'E', 'N')),
  required_nurses integer NOT NULL DEFAULT 5,
  level_mix jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(department, shift_type)
);
COMMENT ON COLUMN public.ward_shift_config.level_mix IS 'e.g. {"1":2,"2":2,"3":1} = 2 junior, 2 mid, 1 senior';
ALTER TABLE public.ward_shift_config ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Managers can manage ward config" ON public.ward_shift_config FOR ALL USING (is_manager()) WITH CHECK (is_manager());
CREATE POLICY "Authenticated can read ward config" ON public.ward_shift_config FOR SELECT USING (auth.uid() IS NOT NULL);

CREATE TRIGGER update_ward_shift_config_updated_at BEFORE UPDATE ON public.ward_shift_config FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- 5. Nurse exclusions (pairs that shouldn't work together)
CREATE TABLE public.nurse_exclusions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nurse_id_1 uuid NOT NULL REFERENCES public.nurses(id) ON DELETE CASCADE,
  nurse_id_2 uuid NOT NULL REFERENCES public.nurses(id) ON DELETE CASCADE,
  reason text,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (nurse_id_1 < nurse_id_2),
  UNIQUE(nurse_id_1, nurse_id_2)
);
ALTER TABLE public.nurse_exclusions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Managers can manage exclusions" ON public.nurse_exclusions FOR ALL USING (is_manager()) WITH CHECK (is_manager());

-- 6. Insert default ward config for General department
INSERT INTO public.ward_shift_config (department, shift_type, required_nurses, level_mix) VALUES
  ('General', 'D', 6, '{"1":2,"2":2,"3":1,"4":1}'),
  ('General', 'E', 5, '{"1":2,"2":2,"3":1}'),
  ('General', 'N', 5, '{"1":2,"2":2,"3":1}');
