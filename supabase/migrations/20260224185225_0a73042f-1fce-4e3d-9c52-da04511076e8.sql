
-- Create a security definer function to get team members (non-sensitive fields only)
-- for nurses in the same department as the authenticated user
CREATE OR REPLACE FUNCTION public.get_department_nurses()
RETURNS TABLE(id uuid, name text, department text)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT n.id, n.name, n.department
  FROM public.nurses n
  WHERE n.invite_status = 'accepted'
    AND n.department = (
      SELECT department FROM public.nurses
      WHERE user_id = auth.uid() AND invite_status = 'accepted'
      LIMIT 1
    )
  ORDER BY n.name;
$$;
