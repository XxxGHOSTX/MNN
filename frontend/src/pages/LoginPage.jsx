import { useState } from "react";
import { toast } from "sonner";
import { Lock, Server, User } from "lucide-react";
import { Card } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { getBackendUrl, setBackendUrl } from "../services/api";

const AUTH_BACKGROUND =
  "https://images.unsplash.com/photo-1698668975271-2ba9a323be6b?crop=entropy&cs=srgb&fm=jpg&q=85";

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123!");
  const [backendUrl, setBackendUrlState] = useState(getBackendUrl());
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      setIsSubmitting(true);
      setBackendUrl(backendUrl);
      await onLogin(username, password);
      toast.success("Authenticated. Dashboard is ready.");
    } catch (error) {
      toast.error(error.message || "Authentication failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="grid min-h-screen grid-cols-1 md:grid-cols-2" data-testid="login-page-root">
      <section className="relative hidden overflow-hidden border-r border-white/10 md:block" data-testid="login-visual-panel">
        <img
          src={AUTH_BACKGROUND}
          alt="Server infrastructure"
          className="h-full w-full object-cover object-center"
          data-testid="login-visual-image"
        />
        <div className="absolute inset-0 bg-black/65 p-10">
          <h1 className="max-w-md text-4xl tracking-tight text-white" data-testid="login-visual-title">
            MNN OPS
          </h1>
          <p className="mt-4 max-w-md text-sm text-zinc-300" data-testid="login-visual-subtitle">
            Deterministic operations console for authentication, query execution, and infrastructure observability.
          </p>
        </div>
      </section>

      <section className="flex items-center justify-center p-6 md:p-10" data-testid="login-form-panel">
        <Card className="fade-in w-full max-w-md bg-black/40 backdrop-blur-sm" data-testid="login-form-card">
          <h2 className="text-2xl font-black tracking-tight" data-testid="login-form-title">
            Operator Login
          </h2>
          <p className="mt-2 text-sm text-zinc-400" data-testid="login-form-description">
            Use your MNN operator credentials to access the dashboard.
          </p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4" data-testid="login-form">
            <label className="block text-sm" data-testid="login-username-label">
              Username
              <div className="relative mt-2">
                <User className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
                <Input
                  data-testid="login-username-input"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="pl-9"
                  autoComplete="username"
                />
              </div>
            </label>

            <label className="block text-sm" data-testid="login-password-label">
              Password
              <div className="relative mt-2">
                <Lock className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
                <Input
                  data-testid="login-password-input"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-9"
                  autoComplete="current-password"
                />
              </div>
            </label>

            <Button
              data-testid="login-advanced-toggle-button"
              variant="ghost"
              className="w-full justify-start"
              onClick={() => setShowAdvanced((value) => !value)}
            >
              <Server className="mr-2 h-4 w-4" />
              {showAdvanced ? "Hide backend settings" : "Show backend settings"}
            </Button>

            {showAdvanced && (
              <label className="block text-sm" data-testid="login-backend-url-label">
                Backend URL
                <Input
                  data-testid="login-backend-url-input"
                  value={backendUrl}
                  onChange={(e) => setBackendUrlState(e.target.value)}
                  placeholder="https://your-backend-host"
                  className="mt-2 font-mono"
                />
              </label>
            )}

            <Button
              data-testid="login-submit-button"
              type="submit"
              className="w-full"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Signing in..." : "Sign in to Dashboard"}
            </Button>
          </form>
        </Card>
      </section>
    </main>
  );
}
