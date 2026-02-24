
-- 1. Add columns to nurses table for invite system
ALTER TABLE public.nurses 
  ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS invite_status text NOT NULL DEFAULT 'pending';

-- 2. Create helper function to check if user is an accepted nurse
CREATE OR REPLACE FUNCTION public.is_accepted_nurse(_user_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.nurses WHERE user_id = _user_id AND invite_status = 'accepted'
  )
$$;

-- 3. Drop all existing RESTRICTIVE policies on nurses
DROP POLICY IF EXISTS "Managers can delete nurses" ON public.nurses;
DROP POLICY IF EXISTS "Managers can insert nurses" ON public.nurses;
DROP POLICY IF EXISTS "Managers can read nurses" ON public.nurses;
DROP POLICY IF EXISTS "Managers can update nurses" ON public.nurses;

-- 4. Drop all existing RESTRICTIVE policies on schedules
DROP POLICY IF EXISTS "Managers can delete schedules" ON public.schedules;
DROP POLICY IF EXISTS "Managers can insert schedules" ON public.schedules;
DROP POLICY IF EXISTS "Managers can read schedules" ON public.schedules;
DROP POLICY IF EXISTS "Managers can update schedules" ON public.schedules;

-- 5. Nurses table - new PERMISSIVE policies
-- Managers have full access
CREATE POLICY "Managers can manage nurses" ON public.nurses
FOR ALL TO authenticated
USING (is_manager())
WITH CHECK (is_manager());

-- Users can see nurse records that match their email (to see pending invites)
CREATE POLICY "Users can see own invite" ON public.nurses
FOR SELECT TO authenticated
USING (email = (auth.jwt() ->> 'email') AND invite_status = 'pending');

-- Users can accept their own invite (set user_id and status)
CREATE POLICY "Users can accept own invite" ON public.nurses
FOR UPDATE TO authenticated
USING (email = (auth.jwt() ->> 'email') AND invite_status = 'pending')
WITH CHECK (user_id = auth.uid() AND invite_status = 'accepted');

-- Accepted nurses can read all nurses (for team schedule view)
CREATE POLICY "Accepted nurses can read all nurses" ON public.nurses
FOR SELECT TO authenticated
USING (is_accepted_nurse(auth.uid()));

-- 6. Schedules table - new PERMISSIVE policies
-- Managers have full access
CREATE POLICY "Managers can manage schedules" ON public.schedules
FOR ALL TO authenticated
USING (is_manager())
WITH CHECK (is_manager());

-- Accepted nurses can read all schedules (team view)
CREATE POLICY "Accepted nurses can read schedules" ON public.schedules
FOR SELECT TO authenticated
USING (is_accepted_nurse(auth.uid()));
