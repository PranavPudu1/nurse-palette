import { createClient } from "https://esm.sh/@supabase/supabase-js@2.49.1";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-supabase-client-platform, x-supabase-client-platform-version, x-supabase-client-runtime, x-supabase-client-runtime-version",
};

type ShiftType = "D" | "E" | "N" | "X";

interface Nurse {
  id: string;
  name: string;
  level: number;
  department: string;
}

interface WardConfig {
  shift_type: string;
  required_nurses: number;
  level_mix: Record<string, number>;
}

interface Preference {
  nurse_id: string;
  prefers_weekend: boolean;
  prefers_night: boolean;
  prefers_weekday: boolean;
}

function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate();
}

function dateKey(year: number, month: number, day: number): string {
  return `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function generateSingleSchedule(
  nurses: Nurse[],
  year: number,
  month: number,
  wardConfigs: WardConfig[],
  preferences: Preference[],
  unavailability: { nurse_id: string; date: string }[],
  exclusions: { nurse_id_1: string; nurse_id_2: string }[],
  randomSeed: number
): Record<string, Record<string, ShiftType>> {
  const days = getDaysInMonth(year, month);
  const schedule: Record<string, Record<string, ShiftType>> = {};
  const unavailMap = new Set(unavailability.map((u) => `${u.nurse_id}:${u.date}`));
  const prefMap = new Map(preferences.map((p) => [p.nurse_id, p]));

  // Initialize all to X
  for (const nurse of nurses) {
    schedule[nurse.id] = {};
    for (let d = 1; d <= days; d++) {
      schedule[nurse.id][dateKey(year, month, d)] = "X";
    }
  }

  // Simple seeded random
  let seed = randomSeed;
  const random = () => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };

  // Shuffle helper
  const shuffle = <T>(arr: T[]): T[] => {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  };

  // Track consecutive working days and night state per nurse
  const state: Record<string, { consecutive: number; nightPair: boolean; restDays: number }> = {};
  for (const n of nurses) {
    state[n.id] = { consecutive: 0, nightPair: false, restDays: 0 };
  }

  // For each day, assign shifts
  for (let d = 1; d <= days; d++) {
    const key = dateKey(year, month, d);
    const dow = new Date(year, month, d).getDay();
    const isWeekend = dow === 0 || dow === 6;

    // Determine shift requirements
    const shiftTypes: ShiftType[] = ["D", "E", "N"];

    for (const shiftType of shiftTypes) {
      const config = wardConfigs.find((c) => c.shift_type === shiftType);
      const needed = config?.required_nurses ?? 2;

      // Find available nurses for this shift
      const available = shuffle(nurses).filter((n) => {
        const s = state[n.id];
        // Already assigned today
        if (schedule[n.id][key] !== "X") return false;
        // Unavailable
        if (unavailMap.has(`${n.id}:${key}`)) return false;
        // Must rest after night pair
        if (s.restDays > 0) return false;
        // Max 4 consecutive
        if (s.consecutive >= 4) return false;
        // Night shift: only assign if they can do 2 consecutive
        if (shiftType === "N" && d < days) {
          const nextKey = dateKey(year, month, d + 1);
          if (unavailMap.has(`${n.id}:${nextKey}`)) return false;
        }
        return true;
      });

      // Score and sort by preference fit
      const scored = available.map((n) => {
        let score = random() * 10; // base randomness
        const pref = prefMap.get(n.id);
        if (pref) {
          if (shiftType === "N" && pref.prefers_night) score += 20;
          if (isWeekend && pref.prefers_weekend) score += 15;
          if (!isWeekend && pref.prefers_weekday) score += 15;
        }
        // Higher level nurses get slight priority for night shifts
        if (shiftType === "N") score += n.level * 2;
        return { nurse: n, score };
      });

      scored.sort((a, b) => b.score - a.score);

      // Assign top N nurses
      let assigned = 0;
      for (const { nurse } of scored) {
        if (assigned >= needed) break;

        // Check exclusions
        const hasExclusion = exclusions.some((e) => {
          const partnerId = e.nurse_id_1 === nurse.id ? e.nurse_id_2 : e.nurse_id_2 === nurse.id ? e.nurse_id_1 : null;
          if (!partnerId) return false;
          return schedule[partnerId]?.[key] === shiftType;
        });
        if (hasExclusion) continue;

        schedule[nurse.id][key] = shiftType;
        assigned++;

        // Update state
        const s = state[nurse.id];
        s.consecutive++;

        if (shiftType === "N") {
          if (!s.nightPair) {
            s.nightPair = true;
          } else {
            // Second night - will need 2 rest days
            s.nightPair = false;
            s.restDays = 2;
          }
        }
      }
    }

    // Update rest days for all nurses
    for (const nurse of nurses) {
      const s = state[nurse.id];
      if (schedule[nurse.id][key] === "X") {
        if (s.restDays > 0) s.restDays--;
        s.consecutive = 0;
        s.nightPair = false;
      }
    }
  }

  // Second pass: assign night shifts in pairs
  for (const nurse of nurses) {
    for (let d = 1; d <= days; d++) {
      const key = dateKey(year, month, d);
      if (schedule[nurse.id][key] === "N") {
        const nextDay = d + 1;
        if (nextDay <= days) {
          const nextKey = dateKey(year, month, nextDay);
          if (schedule[nurse.id][nextKey] === "X" && !unavailMap.has(`${nurse.id}:${nextKey}`)) {
            schedule[nurse.id][nextKey] = "N";
          }
        }
      }
    }
  }

  return schedule;
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

    // Fetch all data
    const [nursesRes, configRes, prefsRes, unavailRes, exclRes] = await Promise.all([
      supabase.from("nurses").select("id, name, level, department").eq("invite_status", "accepted"),
      supabase.from("ward_shift_config").select("*"),
      supabase.from("nurse_preferences").select("*"),
      supabase.from("nurse_unavailability").select("nurse_id, date")
        .gte("date", `${year}-${String(month + 1).padStart(2, "0")}-01`)
        .lte("date", `${year}-${String(month + 1).padStart(2, "0")}-${String(getDaysInMonth(year, month)).padStart(2, "0")}`),
      supabase.from("nurse_exclusions").select("nurse_id_1, nurse_id_2"),
    ]);

    const nurses = (nursesRes.data ?? []) as Nurse[];
    const wardConfigs = (configRes.data ?? []) as WardConfig[];
    const preferences = (prefsRes.data ?? []) as Preference[];
    const unavailability = (unavailRes.data ?? []) as { nurse_id: string; date: string }[];
    const exclusions = (exclRes.data ?? []) as { nurse_id_1: string; nurse_id_2: string }[];

    // Generate 3 options with different random seeds
    const options = [];
    for (let i = 0; i < 3; i++) {
      const seed = Date.now() + i * 7919;
      const schedule = generateSingleSchedule(
        nurses, year, month, wardConfigs, preferences, unavailability, exclusions, seed
      );
      options.push({ id: `option-${i + 1}`, label: `Option ${i + 1}`, schedule });
    }

    return new Response(JSON.stringify({ options }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: (err as Error).message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
