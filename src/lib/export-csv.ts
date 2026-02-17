import { Nurse, ScheduleData, getDaysInMonth, dateKey, ShiftType } from "./scheduler-data";

export function exportScheduleCSV(
  nurses: Nurse[],
  schedule: ScheduleData,
  year: number,
  month: number
) {
  const days = getDaysInMonth(year, month);
  const header = ["Nurse", ...Array.from({ length: days }, (_, i) => String(i + 1))];
  const rows = nurses.map((nurse) => {
    const cells = Array.from({ length: days }, (_, i) => {
      const key = dateKey(year, month, i + 1);
      return (schedule[nurse.id]?.[key] ?? "X") as ShiftType;
    });
    return [nurse.name, ...cells];
  });

  const csv = [header, ...rows].map((r) => r.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `nurse_schedule_${year}_${String(month + 1).padStart(2, "0")}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
