import { createClient } from "https://esm.sh/@supabase/supabase-js@2.49.1";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-supabase-client-platform, x-supabase-client-platform-version, x-supabase-client-runtime, x-supabase-client-runtime-version",
};

function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate();
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

    // Verify the user is a manager
    const token = authHeader?.replace("Bearer ", "");
    const { data: { user }, error: authError } = await supabase.auth.getUser(token);
    if (authError || !user) {
      return new Response(JSON.stringify({ error: "Unauthorized" }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const { data: managerCheck } = await supabase.from("managers").select("id").eq("id", user.id).single();
    if (!managerCheck) {
      return new Response(JSON.stringify({ error: "Not a manager" }), {
        status: 403,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const { year, month } = await req.json();
    const days = getDaysInMonth(year, month);
    const startDate = `${year}-${String(month + 1).padStart(2, "0")}-01`;
    const endDate = `${year}-${String(month + 1).padStart(2, "0")}-${String(days).padStart(2, "0")}`;

    // Fetch all data from database
    const [nursesRes, configRes, prefsRes, unavailRes, exclRes] = await Promise.all([
      supabase.from("nurses").select("id, name, level, department").eq("invite_status", "accepted"),
      supabase.from("ward_shift_config").select("*"),
      supabase.from("nurse_preferences").select("*"),
      supabase.from("nurse_unavailability").select("nurse_id, date")
        .gte("date", startDate)
        .lte("date", endDate),
      supabase.from("nurse_exclusions").select("nurse_id_1, nurse_id_2"),
    ]);

    const nurses = (nursesRes.data ?? []).map((n: any) => ({
      id: n.id,
      name: n.name,
      level: n.level ?? 1,
    }));

    // Convert ward configs to the API format
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

    // Convert unavailability dates to day numbers
    const unavailability = (unavailRes.data ?? []).map((u: any) => ({
      nurse_id: u.nurse_id,
      day: parseInt(u.date.split("-")[2], 10),
    }));

    const exclusions = (exclRes.data ?? []).map((e: any) => ({
      nurse_id_1: e.nurse_id_1,
      nurse_id_2: e.nurse_id_2,
    }));

    // Call the external Python optimizer
    const SCHEDULER_API_URL = Deno.env.get("SCHEDULER_API_URL");
    if (!SCHEDULER_API_URL) {
      return new Response(
        JSON.stringify({ error: "Scheduler API URL not configured. Please add the SCHEDULER_API_URL secret." }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const payload = {
      year,
      month,
      days_in_month: days,
      nurses,
      ward_configs: wardConfigs,
      preferences,
      unavailability,
      exclusions,
      num_options: 3,
      time_limit_seconds: 10.0,
    };

    const optimizerRes = await fetch(`${SCHEDULER_API_URL}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!optimizerRes.ok) {
      const errBody = await optimizerRes.text();
      return new Response(
        JSON.stringify({ error: `Optimizer error (${optimizerRes.status}): ${errBody}` }),
        { status: 502, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const result = await optimizerRes.json();

    return new Response(JSON.stringify(result), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: (err as Error).message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
