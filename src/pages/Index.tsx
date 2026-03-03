import { useAuth } from "@/hooks/useAuth";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { ScheduleTab } from "@/components/ScheduleTab";
import { NursesPanel } from "@/components/NursesPanel";
import { WardConfigPanel } from "@/components/WardConfigPanel";
import { CalendarDays, Users, LogOut, Settings } from "lucide-react";

const Index = () => {
  const { user, signOut } = useAuth();

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card px-6 py-4">
        <div className="max-w-[1600px] mx-auto flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight">Nurse Scheduler</h1>
            <p className="text-sm text-muted-foreground">{user?.email}</p>
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
        <Tabs defaultValue="schedule" className="space-y-6">
          <TabsList>
            <TabsTrigger value="schedule" className="gap-1.5">
              <CalendarDays className="w-4 h-4" /> Schedule
            </TabsTrigger>
            <TabsTrigger value="nurses" className="gap-1.5">
              <Users className="w-4 h-4" /> Nurses
            </TabsTrigger>
            <TabsTrigger value="ward-config" className="gap-1.5">
              <Settings className="w-4 h-4" /> Ward Config
            </TabsTrigger>
          </TabsList>

          <TabsContent value="schedule">
            <ScheduleTab />
          </TabsContent>
          <TabsContent value="nurses">
            <NursesPanel />
          </TabsContent>
          <TabsContent value="ward-config">
            <WardConfigPanel />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default Index;
