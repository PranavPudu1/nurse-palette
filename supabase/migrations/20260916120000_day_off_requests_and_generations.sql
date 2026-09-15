-- Superseded: Lovable applied this migration to the live database and
-- committed its own copy as 20260915184142_6d2800a8 (same DDL for
-- day_off_requests and schedule_generations, plus the grants). Two files
-- creating the same tables would break a fresh replay, so this one is a
-- deliberate no-op kept only because the live migration history may
-- reference its filename.
SELECT 1;
