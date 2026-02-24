-- Ensure newly signed up users are not automatically managers unless bootstrapping first manager
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  -- If this signup matches a pending nurse invite, do not grant manager access
  IF NEW.email IS NOT NULL AND EXISTS (
    SELECT 1
    FROM public.nurses n
    WHERE n.invite_status = 'pending'
      AND n.email IS NOT NULL
      AND lower(n.email) = lower(NEW.email)
  ) THEN
    RETURN NEW;
  END IF;

  -- Bootstrap: only first non-invited account becomes manager
  IF NOT EXISTS (SELECT 1 FROM public.managers) THEN
    INSERT INTO public.managers (id) VALUES (NEW.id)
    ON CONFLICT (id) DO NOTHING;
  END IF;

  RETURN NEW;
END;
$$;

-- Make invite matching case-insensitive for pending invite visibility and acceptance
DROP POLICY IF EXISTS "Users can see own invite" ON public.nurses;
CREATE POLICY "Users can see own invite"
ON public.nurses
FOR SELECT
USING (
  invite_status = 'pending'
  AND email IS NOT NULL
  AND lower(email) = lower(auth.jwt() ->> 'email')
);

DROP POLICY IF EXISTS "Users can accept own invite" ON public.nurses;
CREATE POLICY "Users can accept own invite"
ON public.nurses
FOR UPDATE
USING (
  invite_status = 'pending'
  AND email IS NOT NULL
  AND lower(email) = lower(auth.jwt() ->> 'email')
)
WITH CHECK (
  user_id = auth.uid()
  AND invite_status = 'accepted'
);

-- Performance helper for case-insensitive invite email lookups
CREATE INDEX IF NOT EXISTS idx_nurses_email_lower_pending
ON public.nurses (lower(email))
WHERE invite_status = 'pending';