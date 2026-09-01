import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { Navigate } from "react-router-dom";
import { toast } from "sonner";
import { useLang } from "@/lib/i18n";
import { LanguageToggle } from "@/components/LanguageToggle";

const Auth = () => {
  const { t } = useLang();
  const { user, loading, signIn, signUp } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"manager" | "nurse">("nurse");
  const [submitting, setSubmitting] = useState(false);

  if (loading) return <div className="min-h-screen flex items-center justify-center text-muted-foreground">{t("app.loading")}</div>;
  if (user) return <Navigate to="/" replace />;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (isLogin) {
        await signIn(email, password);
        toast.success(t("auth.signedIn"));
      } else {
        await signUp(email, password, role);
        toast.success(t("auth.created"));
      }
    } catch (err: any) {
      toast.error(err.message || t("auth.failed"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="flex justify-center">
          <LanguageToggle />
        </div>
        <div className="text-center">
          <h1 className="text-2xl font-bold tracking-tight">{t("app.title")}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {isLogin ? t("auth.signInSub") : t("auth.signUpSub")}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium" htmlFor="email">{t("auth.email")}</label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              placeholder="you@hospital.com"
            />
          </div>
          <div>
            <label className="text-sm font-medium" htmlFor="password">{t("auth.password")}</label>
            <input
              id="password"
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              placeholder="••••••••"
            />
          </div>
          {!isLogin && (
            <div>
              <label className="text-sm font-medium">{t("auth.role")}</label>
              <div className="mt-1 flex gap-2">
                <button
                  type="button"
                  onClick={() => setRole("nurse")}
                  className={`flex-1 h-10 rounded-md border text-sm font-medium transition-colors ${
                    role === "nurse"
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-background text-foreground border-input hover:bg-muted"
                  }`}
                >
                  {t("auth.nurse")}
                </button>
                <button
                  type="button"
                  onClick={() => setRole("manager")}
                  className={`flex-1 h-10 rounded-md border text-sm font-medium transition-colors ${
                    role === "manager"
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-background text-foreground border-input hover:bg-muted"
                  }`}
                >
                  {t("auth.manager")}
                </button>
              </div>
            </div>
          )}
          <button
            type="submit"
            disabled={submitting}
            className="w-full h-10 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {submitting ? t("auth.wait") : isLogin ? t("auth.signIn") : t("auth.signUp")}
          </button>
        </form>

        <div className="relative">
          <div className="absolute inset-0 flex items-center"><span className="w-full border-t border-border" /></div>
          <div className="relative flex justify-center text-xs uppercase"><span className="bg-background px-2 text-muted-foreground">{t("auth.or")}</span></div>
        </div>

        <div className="rounded-md border border-border bg-muted/50 p-4 space-y-2 text-sm">
          <p className="font-medium text-foreground">{t("auth.demo")}</p>
          <div className="space-y-1 text-muted-foreground">
            <p><span className="font-medium text-foreground">{t("auth.demoManager")}</span> demomanager@demo.com</p>
            <p><span className="font-medium text-foreground">{t("auth.demoNurse")}</span> demonurse@demo.com</p>
            <p><span className="font-medium text-foreground">{t("auth.demoPassword")}</span> demo123</p>
          </div>
        </div>

        <p className="text-center text-sm text-muted-foreground">
          {isLogin ? t("auth.noAccount") : t("auth.hasAccount")}{" "}
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-primary hover:underline font-medium"
          >
            {isLogin ? t("auth.signUp") : t("auth.signIn")}
          </button>
        </p>
      </div>
    </div>
  );
};

export default Auth;
