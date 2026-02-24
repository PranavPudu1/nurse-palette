import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/hooks/useAuth";
import { useUserRole } from "@/hooks/useUserRole";
import Index from "./pages/Index";
import Auth from "./pages/Auth";
import NurseView from "./pages/NurseView";
import PendingInvite from "./pages/PendingInvite";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center text-muted-foreground">Loading…</div>;
  if (!user) return <Navigate to="/auth" replace />;
  return <>{children}</>;
}

function RoleRouter() {
  const { data: roleData, isLoading } = useUserRole();

  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center text-muted-foreground">Loading…</div>;
  }

  const role = roleData?.role ?? "unknown";

  if (role === "manager") return <Index />;
  if (role === "nurse") return <NurseView />;
  if (role === "pending") return <PendingInvite />;

  // Unknown role - show a message
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="text-center space-y-3">
        <p className="text-muted-foreground">No role assigned. Ask a manager to invite you.</p>
        <SignOutButton />
      </div>
    </div>
  );
}

function SignOutButton() {
  const { signOut } = useAuth();
  return (
    <button onClick={signOut} className="text-sm text-primary hover:underline">
      Sign Out
    </button>
  );
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/auth" element={<Auth />} />
            <Route path="/" element={<ProtectedRoute><RoleRouter /></ProtectedRoute>} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
