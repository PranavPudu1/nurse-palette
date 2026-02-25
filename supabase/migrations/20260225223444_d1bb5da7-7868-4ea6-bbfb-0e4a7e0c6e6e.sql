
-- Update handle_new_user to read role from user metadata
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public'
AS $function$
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

  -- Check if user explicitly chose 'manager' role at signup
  IF (NEW.raw_user_meta_data ->> 'role') = 'manager' THEN
    INSERT INTO public.managers (id) VALUES (NEW.id)
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
  END IF;

  -- Check if user explicitly chose 'nurse' role at signup - create nurse record
  IF (NEW.raw_user_meta_data ->> 'role') = 'nurse' THEN
    INSERT INTO public.nurses (name, user_id, invite_status, email)
    VALUES (
      COALESCE(NEW.raw_user_meta_data ->> 'full_name', split_part(NEW.email, '@', 1)),
      NEW.id,
      'accepted',
      NEW.email
    );
    RETURN NEW;
  END IF;

  -- Fallback: first user becomes manager (bootstrap)
  IF NOT EXISTS (SELECT 1 FROM public.managers) THEN
    INSERT INTO public.managers (id) VALUES (NEW.id)
    ON CONFLICT (id) DO NOTHING;
  END IF;

  RETURN NEW;
END;
$function$;
