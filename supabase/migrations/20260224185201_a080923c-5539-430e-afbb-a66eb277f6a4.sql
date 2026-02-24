
-- 1. Create a public view of nurses that excludes sensitive contact info
CREATE VIEW public.nurses_public
WITH (security_invoker = on) AS
  SELECT id, name, department, user_id, invite_status
  FROM public.nurses;

-- 2. Drop the old permissive SELECT policy for accepted nurses on nurses table
DROP POLICY IF EXISTS "Accepted nurses can read all nurses" ON public.nurses;

-- 3. Accepted nurses can only read their OWN record from the base nurses table
CREATE POLICY "Accepted nurses can read own record"
  ON public.nurses FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

-- 4. Update schedules SELECT policy: nurses can only see schedules for nurses in their department
DROP POLICY IF EXISTS "Accepted nurses can read schedules" ON public.schedules;

CREATE POLICY "Accepted nurses can read department schedules"
  ON public.schedules FOR SELECT
  TO authenticated
  USING (
    is_accepted_nurse(auth.uid())
    AND EXISTS (
      SELECT 1
      FROM public.nurses AS my_nurse
      JOIN public.nurses AS sched_nurse ON sched_nurse.id = nurse_id
      WHERE my_nurse.user_id = auth.uid()
        AND my_nurse.department = sched_nurse.department
    )
  );
