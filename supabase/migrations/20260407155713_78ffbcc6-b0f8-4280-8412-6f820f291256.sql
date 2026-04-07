
-- Create soft_constraints table
CREATE TABLE public.soft_constraints (
  id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  department text NOT NULL DEFAULT 'General',
  constraint_type text NOT NULL,
  nurse_id uuid REFERENCES public.nurses(id) ON DELETE CASCADE,
  params jsonb NOT NULL DEFAULT '{}',
  created_at timestamp with time zone NOT NULL DEFAULT now()
);

ALTER TABLE public.soft_constraints ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Managers can manage soft constraints"
  ON public.soft_constraints FOR ALL
  USING (is_manager())
  WITH CHECK (is_manager());

CREATE POLICY "Nurses can read own soft constraints"
  ON public.soft_constraints FOR SELECT
  USING (nurse_id IN (SELECT id FROM public.nurses WHERE user_id = auth.uid()));

-- Create scheduling_constraints table
CREATE TABLE public.scheduling_constraints (
  id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  department text NOT NULL DEFAULT 'General' UNIQUE,
  max_shifts_per_day integer NOT NULL DEFAULT 1,
  night_window_max integer NOT NULL DEFAULT 1,
  night_window_k integer NOT NULL DEFAULT 3,
  days_off_after_night_block integer NOT NULL DEFAULT 2,
  max_consecutive_workdays integer NOT NULL DEFAULT 4,
  consec_trigger integer NOT NULL DEFAULT 3,
  days_off_after_consec integer NOT NULL DEFAULT 1,
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  created_at timestamp with time zone NOT NULL DEFAULT now()
);

ALTER TABLE public.scheduling_constraints ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Managers can manage scheduling constraints"
  ON public.scheduling_constraints FOR ALL
  USING (is_manager())
  WITH CHECK (is_manager());

CREATE POLICY "Authenticated can read scheduling constraints"
  ON public.scheduling_constraints FOR SELECT
  USING (auth.uid() IS NOT NULL);

-- Insert default row for General department
INSERT INTO public.scheduling_constraints (department) VALUES ('General');

-- Add updated_at trigger for scheduling_constraints
CREATE TRIGGER update_scheduling_constraints_updated_at
  BEFORE UPDATE ON public.scheduling_constraints
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
