
-- Managers table (links auth users to manager role)
CREATE TABLE public.managers (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);
ALTER TABLE public.managers ENABLE ROW LEVEL SECURITY;

-- Nurses table
CREATE TABLE public.nurses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  department TEXT DEFAULT 'General',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);
ALTER TABLE public.nurses ENABLE ROW LEVEL SECURITY;

-- Schedules table
CREATE TABLE public.schedules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nurse_id UUID NOT NULL REFERENCES public.nurses(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  shift_type TEXT NOT NULL DEFAULT 'X' CHECK (shift_type IN ('D', 'N', 'X')),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(nurse_id, date)
);
ALTER TABLE public.schedules ENABLE ROW LEVEL SECURITY;

-- Helper: check if current user is a manager
CREATE OR REPLACE FUNCTION public.is_manager()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.managers WHERE id = auth.uid()
  )
$$;

-- Auto-updated_at trigger
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public;

CREATE TRIGGER update_nurses_updated_at BEFORE UPDATE ON public.nurses FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
CREATE TRIGGER update_schedules_updated_at BEFORE UPDATE ON public.schedules FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Auto-create manager on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.managers (id) VALUES (NEW.id);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

CREATE TRIGGER on_auth_user_created AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- RLS Policies
CREATE POLICY "Managers can view own record" ON public.managers FOR SELECT USING (id = auth.uid());

CREATE POLICY "Managers can read nurses" ON public.nurses FOR SELECT TO authenticated USING (public.is_manager());
CREATE POLICY "Managers can insert nurses" ON public.nurses FOR INSERT TO authenticated WITH CHECK (public.is_manager());
CREATE POLICY "Managers can update nurses" ON public.nurses FOR UPDATE TO authenticated USING (public.is_manager());
CREATE POLICY "Managers can delete nurses" ON public.nurses FOR DELETE TO authenticated USING (public.is_manager());

CREATE POLICY "Managers can read schedules" ON public.schedules FOR SELECT TO authenticated USING (public.is_manager());
CREATE POLICY "Managers can insert schedules" ON public.schedules FOR INSERT TO authenticated WITH CHECK (public.is_manager());
CREATE POLICY "Managers can update schedules" ON public.schedules FOR UPDATE TO authenticated USING (public.is_manager());
CREATE POLICY "Managers can delete schedules" ON public.schedules FOR DELETE TO authenticated USING (public.is_manager());
