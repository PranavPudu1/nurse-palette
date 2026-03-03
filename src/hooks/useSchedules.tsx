import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import type { ShiftType, ScheduleData } from "@/lib/scheduler-data";
import { getDaysInMonth, dateKey } from "@/lib/scheduler-data";

export function useSchedules(year: number, month: number) {
  const startDate = `${year}-${String(month + 1).padStart(2, "0")}-01`;
  const days = getDaysInMonth(year, month);
  const endDate = `${year}-${String(month + 1).padStart(2, "0")}-${String(days).padStart(2, "0")}`;

  return useQuery<ScheduleData>({
    queryKey: ["schedules", year, month],
    queryFn: async () => {
      const { data, error } = await supabase
        .from("schedules")
        .select("nurse_id, date, shift_type")
        .gte("date", startDate)
        .lte("date", endDate);
      if (error) throw error;

      const schedule: ScheduleData = {};
      for (const row of data) {
        if (!schedule[row.nurse_id]) schedule[row.nurse_id] = {};
        schedule[row.nurse_id][row.date] = row.shift_type as ShiftType;
      }
      return schedule;
    },
  });
}

export function useUpsertShift() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ nurseId, date, shiftType }: { nurseId: string; date: string; shiftType: ShiftType }) => {
      const { error } = await supabase
        .from("schedules")
        .upsert({ nurse_id: nurseId, date, shift_type: shiftType }, { onConflict: "nurse_id,date" });
      if (error) throw error;
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ["schedules"] }),
  });
}
