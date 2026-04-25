import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, clearAuthTokens, setAuthTokens } from "../services/api";
import { logout as logoutRequest } from "../services/endpoints";

type Viewer = {
  id: string;
  username: string;
  email?: string | null;
  roles: string[];
  is_active: boolean;
};

type AuthContextValue = {
  viewer: Viewer | null;
  isAuthenticated: boolean;
  status: string | null;
  login: (username: string, password: string, totpCode?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshViewer: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [viewer, setViewer] = useState<Viewer | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  const refreshViewer = async () => {
    try {
      const { data } = await api.get("/api/v1/users/me");
      setViewer(data);
      setStatus(null);
    } catch {
      setViewer(null);
    }
  };

  useEffect(() => {
    if (localStorage.getItem("AUTH_TOKEN")) {
      refreshViewer();
    }
  }, []);

  const login = async (username: string, password: string, totpCode?: string) => {
    setStatus("Signing in...");
    const { data } = await api.post("/api/v1/auth/login", {
      username,
      password,
      totp_code: totpCode || undefined,
    });
    setAuthTokens(data.access_token, data.refresh_token);
    await refreshViewer();
    setStatus("Authenticated");
  };

  const logout = async () => {
    try {
      await logoutRequest();
    } catch {
      // Token may already be expired; local logout still clears the session.
    }
    clearAuthTokens();
    setViewer(null);
    setStatus("Signed out");
  };

  const value = useMemo(
    () => ({
      viewer,
      isAuthenticated: Boolean(viewer),
      status,
      login,
      logout,
      refreshViewer,
    }),
    [viewer, status],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return value;
}
