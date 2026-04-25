import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import clsx from "clsx";
import { navigation } from "../data/navigation";
import { api } from "../services/api";
import { useAuth } from "../context/AuthContext";

export function formatLoginError(err: unknown): string {
  const payload = err as {
    code?: string;
    message?: string;
    response?: { status?: number; data?: { detail?: string } };
  };
  const status = payload?.response?.status;
  const detail = payload?.response?.data?.detail;

  if (status === 401) {
    return (
      "Unauthorized: check credentials. For a fresh local setup, run backend startup once to " +
      "auto-bootstrap dev admin (default admin/admin123 unless overridden)."
    );
  }
  if (status === 404) {
    return "Login endpoint not found. Verify API base URL and backend startup.";
  }
  if (status && status >= 500) {
    return `Backend error (${status}). Check server logs and DB bootstrap state.`;
  }
  if (payload?.code === "ECONNABORTED" || payload?.message?.includes("timeout")) {
    return "Login timed out. Confirm backend is reachable.";
  }
  if (detail && typeof detail === "string") {
    return detail;
  }
  if (payload?.message) {
    return payload.message;
  }
  return "Login failed. Check backend availability and credentials.";
}

export default function Sidebar() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isAuthed, setIsAuthed] = useState(false);
  const [totpCode, setTotpCode] = useState("");
  const auth = useAuth();

  useEffect(() => {
    setIsAuthed(Boolean(localStorage.getItem("AUTH_TOKEN")));
  }, []);

  const handleLogin = async () => {
    setIsLoading(true);
    setStatus(null);
    try {
      const { data } = await api.post("/api/v1/auth/login", {
        username,
        password,
        totp_code: totpCode || undefined,
      });
      if (!data?.access_token) {
        setStatus("Login failed: missing token");
        return;
      }
      localStorage.setItem("AUTH_TOKEN", data.access_token);
      if (data.refresh_token) {
        localStorage.setItem("REFRESH_TOKEN", data.refresh_token);
      }
      await auth.refreshViewer();
      setIsAuthed(true);
      setPassword("");
      setTotpCode("");
      setStatus("Authenticated");
    } catch (err: unknown) {
      setStatus(formatLoginError(err));
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("AUTH_TOKEN");
    localStorage.removeItem("REFRESH_TOKEN");
    setIsAuthed(false);
    setStatus("Signed out");
  };

  return (
    <aside className="w-full border-b border-line bg-white px-6 py-6 md:w-64 md:border-b-0 md:border-r md:min-h-screen">
      {/* Logo */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500 text-sm font-bold text-slate-900">
          PN
        </div>
        <div>
          <p className="text-lg font-bold text-ink">Sentifargo</p>
          <p className="text-xs text-fog">AI Command Surface</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="mt-10 space-y-2">
        {navigation.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === "/"}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all",
                isActive
                  ? "bg-moss/10 text-moss border border-moss/30"
                  : "text-fog hover:text-ink hover:bg-sand"
              )
            }
          >
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Access */}
      <div className="mt-10">
        <p className="text-xs uppercase tracking-wider text-slate-500 font-medium mb-4">
          Access
        </p>
        <div className="space-y-2">
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Username"
            className="w-full rounded-lg border border-line bg-white px-3 py-2 text-sm text-ink placeholder:text-slate-400"
          />
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            placeholder="Password"
            className="w-full rounded-lg border border-line bg-white px-3 py-2 text-sm text-ink placeholder:text-slate-400"
          />
          <input
            value={totpCode}
            onChange={(e) => setTotpCode(e.target.value)}
            placeholder="TOTP code"
            className="w-full rounded-lg border border-line bg-white px-3 py-2 text-sm text-ink placeholder:text-slate-400"
          />
          <button
            onClick={handleLogin}
            disabled={isLoading || !username || !password}
            className="w-full rounded-lg border border-moss bg-moss px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {isLoading ? "Signing in..." : isAuthed ? "Re-authenticate" : "Sign in"}
          </button>
          {isAuthed && (
            <button
              onClick={handleLogout}
              className="w-full rounded-lg border border-line bg-sand px-3 py-2 text-sm font-medium text-ink"
            >
              Sign out
            </button>
          )}
          {status && <p className="text-xs text-fog">{status}</p>}
          <p className="text-[11px] text-fog">Use dev bootstrap credentials locally.</p>
        </div>
      </div>

      {/* Skills */}
      <div className="mt-10">
        <p className="text-xs uppercase tracking-wider text-slate-500 font-medium mb-4">Core Skills</p>
        <div className="flex flex-wrap gap-2">
          {["Python", "React", "ML/AI", "FastAPI", "Docker"].map((skill) => (
            <span
              key={skill}
              className="rounded-md border border-line bg-sand px-2 py-1 text-xs text-ink"
            >
              {skill}
            </span>
          ))}
        </div>
      </div>

      {/* Contact Links */}
      <div className="mt-10">
        <p className="text-xs uppercase tracking-wider text-slate-500 font-medium mb-4">Connect</p>
        <div className="space-y-3">
          <a
            href="https://github.com/Pratikn03"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-fog transition-colors hover:text-moss"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
            </svg>
            GitHub
          </a>
          <a
            href="https://linkedin.com/in/pratiknarwadkar"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-fog transition-colors hover:text-moss"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
            </svg>
            LinkedIn
          </a>
        </div>
      </div>
    </aside>
  );
}
