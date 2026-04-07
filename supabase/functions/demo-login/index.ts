import { createClient } from "https://esm.sh/@supabase/supabase-js@2.49.1";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  const supabaseAdmin = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );

  const managerEmail = "demomanager@demo.com";
  const nurseEmail = "demonurse@demo.com";
  const password = "demo123";

  const ensureUser = async (email: string) => {
    const { data: signIn } = await supabaseAdmin.auth.signInWithPassword({ email, password });
    if (signIn.user) return signIn.user;

    const { data: created, error } = await supabaseAdmin.auth.admin.createUser({
      email,
      password,
      email_confirm: true,
    });
    if (error) throw error;
    return created.user;
  };

  const seedDemoData = async (managerNurses: { nurse_id: string }[]) => {
    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const shifts = ["D", "N", "X"];
    const rows: { nurse_id: string; date: string; shift_type: string }[] = [];

    for (const { nurse_id } of managerNurses) {
      for (let d = 1; d <= daysInMonth; d++) {
        const shift = shifts[Math.floor(Math.random() * shifts.length)];
        if (shift !== "X") {
          const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
          rows.push({ nurse_id, date: dateStr, shift_type: shift });
        }
      }
    }

    if (rows.length > 0) {
      await supabaseAdmin.from("schedules").insert(rows);
    }
  };

  const seedPreferencesAndConstraints = async (
    nurseId: string,
    extras: { id: string; name: string }[]
  ) => {
    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth();
    const pad = (n: number) => String(n).padStart(2, "0");

    const sarah = extras.find((n) => n.name === "Sarah Johnson");
    const emily = extras.find((n) => n.name === "Emily Davis");

    // 1. Nurse preferences
    const prefs = [
      { nurse_id: nurseId, prefers_weekday: true, prefers_night: true, prefers_weekend: false },
      ...(sarah ? [{ nurse_id: sarah.id, prefers_weekday: false, prefers_night: false, prefers_weekend: true }] : []),
      ...(emily ? [{ nurse_id: emily.id, prefers_weekday: true, prefers_night: false, prefers_weekend: false }] : []),
    ];
    for (const p of prefs) {
      await supabaseAdmin.from("nurse_preferences").upsert(p, { onConflict: "nurse_id" });
    }

    // 2. Unavailability
    const unavail = [
      { nurse_id: nurseId, date: `${year}-${pad(month + 1)}-10`, reason: "Vacation" },
      { nurse_id: nurseId, date: `${year}-${pad(month + 1)}-11`, reason: "Vacation" },
      ...(sarah ? [{ nurse_id: sarah.id, date: `${year}-${pad(month + 1)}-20`, reason: "Appointment" }] : []),
    ];
    for (const u of unavail) {
      const { count } = await supabaseAdmin
        .from("nurse_unavailability")
        .select("id", { count: "exact", head: true })
        .eq("nurse_id", u.nurse_id)
        .eq("date", u.date);
      if (!count || count === 0) {
        await supabaseAdmin.from("nurse_unavailability").insert(u);
      }
    }

    // 3. Soft constraints
    const softRows = [
      { nurse_id: nurseId, constraint_type: "avoid_night", department: "ICU", params: { weight: 80 } },
      ...(sarah ? [{ nurse_id: sarah.id, constraint_type: "soft_unavail", department: "ICU", params: { day: 15, slot: 1, weight: 60 } }] : []),
      ...(emily ? [
        { nurse_id: emily.id, constraint_type: "prefer_night", department: "ICU", params: { weight: 70 } },
        { nurse_id: emily.id, constraint_type: "soft_max_nights", department: "ICU", params: { max: 3, weight: 50 } },
      ] : []),
      { nurse_id: null as string | null, constraint_type: "level_night_penalty", department: "ICU", params: { penalties: { "1": 10, "2": 25, "3": 50 }, weight: 40 } },
    ];
    const { count: scCount } = await supabaseAdmin
      .from("soft_constraints")
      .select("id", { count: "exact", head: true })
      .eq("department", "ICU");
    if (!scCount || scCount === 0) {
      await supabaseAdmin.from("soft_constraints").insert(softRows);
    }
  };

  try {
    // 1. Create manager
    const managerUser = await ensureUser(managerEmail);
    await supabaseAdmin.from("managers").upsert({ id: managerUser.id });

    // 2. Create nurse user
    const nurseUser = await ensureUser(nurseEmail);

    // 3. Ensure nurse record exists
    const { data: existingNurse } = await supabaseAdmin
      .from("nurses")
      .select("id")
      .eq("email", nurseEmail)
      .maybeSingle();

    let nurseId: string;
    if (existingNurse) {
      nurseId = existingNurse.id;
      await supabaseAdmin.from("nurses").update({ user_id: nurseUser.id, invite_status: "accepted" }).eq("id", nurseId);
    } else {
      const { data: newNurse } = await supabaseAdmin
        .from("nurses")
        .insert({ name: "Demo Nurse", email: nurseEmail, department: "ICU", user_id: nurseUser.id, invite_status: "accepted" })
        .select()
        .single();
      nurseId = newNurse!.id;
    }

    // 4. Seed additional nurses + schedules if empty
    const { count } = await supabaseAdmin.from("nurses").select("id", { count: "exact", head: true });
    if (count && count <= 1) {
      const { data: extras } = await supabaseAdmin
        .from("nurses")
        .insert([
          { name: "Sarah Johnson", department: "ICU", invite_status: "pending" },
          { name: "Mike Chen", department: "ER", invite_status: "pending" },
          { name: "Emily Davis", department: "ICU", invite_status: "pending" },
        ])
        .select();

      const allNurseIds = [{ nurse_id: nurseId }, ...(extras || []).map((n) => ({ nurse_id: n.id }))];
      await seedDemoData(allNurseIds);
    }

    return new Response(JSON.stringify({ ok: true }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (error: any) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
