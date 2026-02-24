-- Ensure nurse schedule visibility checks are not blocked by nurses table RLS
CREATE OR REPLACE FUNCTION public.can_read_schedule_for_department(_nurse_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM public.nurses me
    JOIN public.nurses target ON target.id = _nurse_id
    WHERE me.user_id = auth.uid()
      AND me.invite_status = 'accepted'
      AND target.department = me.department
  );
$$;

-- Replace schedule read policy for nurses to use security-definer function
DROP POLICY IF EXISTS "Accepted nurses can read department schedules" ON public.schedules;

CREATE POLICY "Accepted nurses can read department schedules"
ON public.schedules
FOR SELECT
USING (
  public.is_accepted_nurse(auth.uid())
  AND public.can_read_schedule_for_department(schedules.nurse_id)
);