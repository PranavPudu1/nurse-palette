import { createClient } from "https://esm.sh/@supabase/supabase-js@2.49.1";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-supabase-client-platform, x-supabase-client-platform-version, x-supabase-client-runtime, x-supabase-client-runtime-version",
};

function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate();
}

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

interface RequestBody {
  year: number;
  month: number;
  extra_unavailability?: { nurse_id: string; date: string }[];
  num_options?: number;
  /** "generate" (default) or "temp_variants". */
  mode?: string;
  /** temp_variants only: how many temp nurses to try, ascending. */
  temp_counts?: number[];
}

/**
 * Assemble the optimizer payload from the database.
 *
 * Extracted so the plain generate path and the temp-variant path cannot drift:
 * a variant is the same ward, the same rules and the same people, with extra
 * nurses added solver-side.
 */
async function buildPayload(supabase: any, body: RequestBody) {
  const { year, month, extra_unavailability, num_options } = body;
  const days = getDaysInMonth(year, month);
  const startDate = `${year}-${String(month + 1).padStart(2, "0")}-01`;
  const endDate = `${year}-${String(month + 1).padStart(2, "0")}-${String(days).padStart(2, "0")}`;

  // Fetch all data
  const [nursesRes, configRes, prefsRes, unavailRes, exclRes, softConRes, hardConRes] = await Promise.all([
    supabase.from("nurses")
      .select("id, name, level, department, employment_type, available_from, available_until")
      .eq("invite_status", "accepted"),
    supabase.from("ward_shift_config").select("*"),
    supabase.from("nurse_preferences").select("*"),
    supabase.from("nurse_unavailability").select("nurse_id, date")
      .gte("date", startDate)
      .lte("date", endDate),
    supabase.from("nurse_exclusions").select("nurse_id_1, nurse_id_2"),
    supabase.from("soft_constraints").select("*"),
    supabase.from("scheduling_constraints").select("*").eq("department", "General").single(),
  ]);

  // A contract window is stored as dates but the solver indexes days of the
  // month, so clamp it here. A nurse whose window does not overlap this month
  // stays in the payload with an empty window rather than being dropped: their
  // row should show as unavailable, not vanish from the grid.
  const toDay = (iso: string | null, fallback: number | null): number | null => {
    if (!iso) return fallback;
    if (iso < startDate) return fallback;
    if (iso > endDate) return null;
    return parseInt(iso.slice(8, 10), 10);
  };

  const nurses = (nursesRes.data ?? []).map((n: any) => {
    const startsAfterMonth = n.available_from && n.available_from > endDate;
    const endsBeforeMonth = n.available_until && n.available_until < startDate;
    return {
      id: n.id,
      name: n.name,
      level: n.level ?? 1,
      is_temp: n.employment_type === "temp",
      // lo > hi means "not available at all this month", which pins the row off.
      available_from_day: startsAfterMonth ? days + 1 : toDay(n.available_from, null),
      available_until_day: endsBeforeMonth ? 0 : toDay(n.available_until, null),
    };
  });

  const wardConfigs = (configRes.data ?? []).map((c: any) => {
    const levelMix = (typeof c.level_mix === "object" && c.level_mix !== null) ? c.level_mix : {};
    return {
      shift_type: c.shift_type,
      required_nurses: c.required_nurses ?? 2,
      min_high: (levelMix as Record<string, number>)["2"] ?? 1,
    };
  });

  const preferences = (prefsRes.data ?? []).map((p: any) => ({
    nurse_id: p.nurse_id,
    prefers_weekend: p.prefers_weekend ?? false,
    prefers_night: p.prefers_night ?? false,
    prefers_weekday: p.prefers_weekday ?? false,
  }));

  const unavailability = (unavailRes.data ?? []).map((u: any) => ({
    nurse_id: u.nurse_id,
    day: parseInt(u.date.split("-")[2], 10),
  }));

  // What-if previews pass hypothetical days off (e.g. "as if this pending
  // request were approved") without writing them to the database.
  for (const u of (extra_unavailability ?? [])) {
    if (u?.nurse_id && typeof u?.date === "string"
        && u.date >= startDate && u.date <= endDate) {
      unavailability.push({
        nurse_id: u.nurse_id,
        day: parseInt(u.date.split("-")[2], 10),
      });
    }
  }

  const exclusions = (exclRes.data ?? []).map((e: any) => ({
    nurse_id_1: e.nurse_id_1,
    nurse_id_2: e.nurse_id_2,
  }));

  // Map soft_constraints from DB
  const softConstraints = (softConRes.data ?? []).map((sc: any) => ({
    constraint_type: sc.constraint_type,
    nurse_id: sc.nurse_id ?? null,
    params: sc.params ?? {},
  }));

  // Also map nurse_preferences into soft constraints for backward compat
  for (const p of preferences) {
    if (p.prefers_weekend) {
      softConstraints.push({
        constraint_type: "prefer_weekend",
        nurse_id: p.nurse_id,
        params: { weight: 50 },
      });
    }
    if (p.prefers_weekday) {
      softConstraints.push({
        constraint_type: "prefer_weekday",
        nurse_id: p.nurse_id,
        params: { weight: 40 },
      });
    }
    if (p.prefers_night) {
      softConstraints.push({
        constraint_type: "prefer_night",
        nurse_id: p.nurse_id,
        params: { weight: 80 },
      });
    }
  }

  // Hard constraints from DB
  const hc = hardConRes.data;
  const hardConstraints = hc ? {
    max_shifts_per_day: hc.max_shifts_per_day,
    night_window_max: hc.night_window_max,
    night_window_k: hc.night_window_k,
    days_off_after_night_block: hc.days_off_after_night_block,
    max_consecutive_workdays: hc.max_consecutive_workdays,
    consec_trigger: hc.consec_trigger,
    days_off_after_consec: hc.days_off_after_consec,
  } : undefined;

  return {
    year,
    month,
    days_in_month: days,
    nurses,
    ward_configs: wardConfigs,
    preferences,
    unavailability,
    exclusions,
    soft_constraints: softConstraints,
    hard_constraints: hardConstraints,
    num_options: num_options ?? 3,
    time_limit_seconds: 10.0,
  };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const authHeader = req.headers.get("Authorization");
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    );

    const token = authHeader?.replace("Bearer ", "");
    const { data: { user }, error: authError } = await supabase.auth.getUser(token);
    if (authError || !user) return json({ error: "Unauthorized" }, 401);

    const { data: managerCheck } = await supabase.from("managers").select("id").eq("id", user.id).single();
    if (!managerCheck) return json({ error: "Not a manager" }, 403);

    const body: RequestBody = await req.json();

    const SCHEDULER_API_URL = Deno.env.get("SCHEDULER_API_URL");
    if (!SCHEDULER_API_URL) {
      // 200 with a code, not 500: supabase-js discards the body of a non-2xx
      // response, so a 500 would reach the client as an opaque
      // "Edge Function returned a non-2xx status code".
      return json({ error: "Scheduler API URL not configured.", code: "not_configured" });
    }

    const payload = await buildPayload(supabase, body);

    const tempMode = body.mode === "temp_variants";
    const route = tempMode ? "/generate-temp-variants" : "/generate";
    const sent = tempMode
      ? { ...payload, temp_counts: body.temp_counts ?? [1, 2, 3] }
      : payload;

    const optimizerRes = await fetch(`${SCHEDULER_API_URL}${route}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(sent),
    });

    if (!optimizerRes.ok) {
      const errBody = await optimizerRes.text();
      // Surface the optimizer's own reason. It must come back as a 200 so the
      // client can read it: supabase-js throws away the body of any non-2xx
      // response and substitutes a fixed string, which is why the infeasible
      // branch in ScheduleTab used to be unreachable.
      let code = "optimizer_error";
      let message = `Optimizer error (${optimizerRes.status}): ${errBody}`;
      try {
        const parsed = JSON.parse(errBody);
        if (parsed?.detail && typeof parsed.detail === "object") {
          code = parsed.detail.code ?? code;
          message = parsed.detail.message ?? message;
        } else if (typeof parsed?.detail === "string") {
          message = parsed.detail;
        }
      } catch {
        // Non-JSON body: keep the raw text.
      }
      return json({ error: message, code });
    }

    return json(await optimizerRes.json());
  } catch (err) {
    return json({ error: (err as Error).message, code: "unexpected" }, 500);
  }
});
