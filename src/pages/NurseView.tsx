import { useState, useMemo } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useNurses } from "@/hooks/useNurses";
import { useDepartmentNurses } from "@/hooks/useDepartmentNurses";
import { useSchedules } from "@/hooks/useSchedules";
import { ScheduleGrid } from "@/components/ScheduleGrid";
import { MonthSelector } from "@/components/MonthSelector";
import { Legend } from "@/components/Legend";
import { NursePreferencesPanel } from "@/components/NursePreferencesPanel";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { CalendarDays, Users, LogOut, Settings2 } from "lucide-react";

const now = new Date();

const NurseView = () => {
  const { user, signOut } = useAuth();
  const { data: nurses = [] } = useNurses();
  const { data: departmentNurses = [] } = useDepartmentNurses();

  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth());
  const { data: schedule = {}, isLoading } = useSchedules(year, month);

  const prevMonth = () => {
    if (month === 0) { setMonth(11); setYear(y => y - 1); }
    else setMonth(m => m - 1);
  };
  const nextMonth = () => {
    if (month === 11) { setMonth(0); setYear(y => y + 1); }
    else setMonth(m => m + 1);
  };

  const myNurse = nurses.find(n => n.user_id === user?.id);

  const myGridNurses = useMemo(() =>
    myNurse ? [{ id: myNurse.id, name: myNurse.name }] : [],
    [myNurse]
  );

  const allGridNurses = useMemo(() =>
    departmentNurses.map(n => ({ id: n.id, name: n.name })),
    [departmentNurses]
  );

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card px-6 py-4">
        <div className="max-w-[1600px] mx-auto flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight">Nurse Scheduler</h1>
            <p className="text-sm text-muted-foreground">
              {myNurse?.name ?? user?.email} · {myNurse?.department ?? "Nurse"}
            </p>
          </div>
          <button
            onClick={signOut}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-secondary text-secondary-foreground hover:bg-accent transition-colors"
          >
            <LogOut className="w-4 h-4" /> Sign Out
          </button>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-6 py-6">
        <Tabs defaultValue="my-schedule" className="space-y-6">
          <TabsList>
            <TabsTrigger value="my-schedule" className="gap-1.5">
              <CalendarDays className="w-4 h-4" /> My Schedule
            </TabsTrigger>
            <TabsTrigger value="team" className="gap-1.5">
              <Users className="w-4 h-4" /> Team Schedule
            </TabsTrigger>
            <TabsTrigger value="preferences" className="gap-1.5">
              <Settings2 className="w-4 h-4" /> Preferences
            </TabsTrigger>
          </TabsList>

          <TabsContent value="my-schedule">
            <div className="space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
                <MonthSelector year={year} month={month} onPrev={prevMonth} onNext={nextMonth} />
                <Legend />
              </div>
              {isLoading ? (
                <div className="py-12 text-center text-muted-foreground">Loading schedule…</div>
              ) : !myNurse ? (
                <div className="py-12 text-center text-muted-foreground">No schedule assigned yet.</div>
              ) : (
                <ScheduleGrid
                  nurses={myGridNurses}
                  schedule={schedule}
                  year={year}
                  month={month}
                  readOnly={true}
                />
              )}
            </div>
          </TabsContent>

          <TabsContent value="team">
            <div className="space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
                <MonthSelector year={year} month={month} onPrev={prevMonth} onNext={nextMonth} />
                <Legend />
              </div>
              {isLoading ? (
                <div className="py-12 text-center text-muted-foreground">Loading schedule…</div>
              ) : allGridNurses.length === 0 ? (
                <div className="py-12 text-center text-muted-foreground">No team members yet.</div>
              ) : (
                <ScheduleGrid
                  nurses={allGridNurses}
                  schedule={schedule}
                  year={year}
                  month={month}
                  readOnly={true}
                />
              )}
            </div>
          </TabsContent>

          <TabsContent value="preferences">
            {myNurse ? (
              <NursePreferencesPanel nurseId={myNurse.id} />
            ) : (
              <div className="py-12 text-center text-muted-foreground">No nurse profile found.</div>
            )}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default NurseView;
