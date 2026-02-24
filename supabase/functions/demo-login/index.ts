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

  const demoEmail = "demo@nursescheduler.app";
  const demoPassword = "demo123456";

  try {
    // Try signing in first to check if account exists
    const { data: signInData, error: signInError } =
      await supabaseAdmin.auth.signInWithPassword({
        email: demoEmail,
        password: demoPassword,
      });

    if (!signInError && signInData.user) {
      // Account exists, return credentials
      return new Response(
        JSON.stringify({ email: demoEmail, password: demoPassword }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Account doesn't exist, create it
    const { data: createData, error: createError } =
      await supabaseAdmin.auth.admin.createUser({
        email: demoEmail,
        password: demoPassword,
        email_confirm: true,
      });
    if (createError) throw createError;

    // Wait for trigger to create manager record
    await new Promise((r) => setTimeout(r, 500));

    // Seed demo nurses
    const { data: nurses } = await supabaseAdmin
      .from("nurses")
      .insert([
        { name: "Sarah Johnson", email: "sarah@hospital.com", department: "ICU", invite_status: "pending" },
        { name: "Mike Chen", email: "mike@hospital.com", department: "ER", invite_status: "pending" },
        { name: "Emily Davis", email: "emily@hospital.com", department: "Pediatrics", invite_status: "pending" },
        { name: "Raj Patel", email: "raj@hospital.com", department: "Surgery", invite_status: "pending" },
      ])
      .select();

    // Seed schedules for current month
    if (nurses && nurses.length > 0) {
      const today = new Date();
      const year = today.getFullYear();
      const month = today.getMonth();
      const daysInMonth = new Date(year, month + 1, 0).getDate();
      const shifts = ["D", "N", "X"];
      const rows: { nurse_id: string; date: string; shift_type: string }[] = [];

      for (const nurse of nurses) {
        for (let d = 1; d <= daysInMonth; d++) {
          const shift = shifts[Math.floor(Math.random() * shifts.length)];
          if (shift !== "X") {
            const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
            rows.push({ nurse_id: nurse.id, date: dateStr, shift_type: shift });
          }
        }
      }

      if (rows.length > 0) {
        await supabaseAdmin.from("schedules").insert(rows);
      }
    }

    return new Response(
      JSON.stringify({ email: demoEmail, password: demoPassword }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (error: any) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
