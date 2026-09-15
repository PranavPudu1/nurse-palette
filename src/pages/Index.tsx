import { useAuth } from "@/hooks/useAuth";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { ScheduleTab } from "@/components/ScheduleTab";
import { NursesPanel } from "@/components/NursesPanel";
import { WardConfigPanel } from "@/components/WardConfigPanel";
import { SchedulingRulesPanel } from "@/components/SchedulingRulesPanel";
import { RequestsPanel } from "@/components/RequestsPanel";
import { CalendarDays, Users, LogOut, Settings, Sliders, Inbox } from "lucide-react";
import { LanguageToggle } from "@/components/LanguageToggle";
import { useLang } from "@/lib/i18n";

const Index = () => {
  const { user, signOut } = useAuth();
  const { t } = useLang();

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card px-6 py-4">
        <div className="max-w-[1600px] mx-auto flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight">{t("app.title")}</h1>
            <p className="text-sm text-muted-foreground">{user?.email}</p>
          </div>
          <div className="flex items-center gap-3">
            <LanguageToggle />
            <button
              onClick={signOut}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md bg-secondary text-secondary-foreground hover:bg-accent transition-colors"
            >
              <LogOut className="w-4 h-4" /> {t("app.signOut")}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-6 py-6">
        <Tabs defaultValue="schedule" className="space-y-6">
          <TabsList>
            <TabsTrigger value="schedule" className="gap-1.5">
              <CalendarDays className="w-4 h-4" /> {t("tab.schedule")}
            </TabsTrigger>
            <TabsTrigger value="nurses" className="gap-1.5">
              <Users className="w-4 h-4" /> {t("tab.nurses")}
            </TabsTrigger>
            <TabsTrigger value="requests" className="gap-1.5">
              <Inbox className="w-4 h-4" /> {t("tab.requests")}
            </TabsTrigger>
            <TabsTrigger value="ward-config" className="gap-1.5">
              <Settings className="w-4 h-4" /> {t("tab.wardConfig")}
            </TabsTrigger>
            <TabsTrigger value="rules" className="gap-1.5">
              <Sliders className="w-4 h-4" /> {t("tab.rules")}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="schedule">
            <ScheduleTab />
          </TabsContent>
          <TabsContent value="nurses">
            <NursesPanel />
          </TabsContent>
          <TabsContent value="requests">
            <RequestsPanel />
          </TabsContent>
          <TabsContent value="ward-config">
            <WardConfigPanel />
          </TabsContent>
          <TabsContent value="rules">
            <SchedulingRulesPanel />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default Index;
