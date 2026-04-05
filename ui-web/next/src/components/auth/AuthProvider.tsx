"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useQuery } from "@apollo/client";
import { usePathname, useRouter } from "next/navigation";
import { VIEWER } from "@/lib/gateway-graphql";
import {
  AUTH_EVENT,
  clearAuthSession,
  getAuthToken,
} from "@/lib/auth";
import { getAuthMode, type AuthMode } from "@/lib/runtime";

type Viewer = {
  id: string;
  username: string;
  email?: string | null;
  roles: string[];
  isActive: boolean;
};

type AuthContextValue = {
  authMode: AuthMode;
  authenticated: boolean;
  viewer: Viewer | null;
  loading: boolean;
  authError: string | null;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function isUnauthorizedMessage(message: string | undefined): boolean {
  const text = String(message ?? "").toLowerCase();
  return (
    text.includes("unauthorized") ||
    text.includes("forbidden") ||
    text.includes("invalid token") ||
    text.includes("user inactive") ||
    text.includes("401")
  );
}

function AuthLoadingState() {
  return (
    <div className="sf-page-stack">
      <section className="card panel-grid">
        <div className="sf-panel-heading">Authenticating</div>
        <p className="muted">Verifying operator session and runtime access.</p>
      </section>
    </div>
  );
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const authMode = getAuthMode();
  const [hydrated, setHydrated] = useState(false);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const syncToken = () => setToken(getAuthToken());
    syncToken();
    setHydrated(true);
    window.addEventListener(AUTH_EVENT, syncToken);
    return () => window.removeEventListener(AUTH_EVENT, syncToken);
  }, []);

  const viewerQuery = useQuery<{ viewer: Viewer | null }>(VIEWER, {
    skip: authMode !== "jwt" || !hydrated || !token,
    fetchPolicy: "cache-and-network",
  });

  useEffect(() => {
    if (!hydrated || authMode !== "jwt") return;
    if (!token && pathname !== "/login") {
      router.replace("/login");
    }
  }, [authMode, hydrated, pathname, router, token]);

  useEffect(() => {
    if (authMode !== "jwt" || !token) return;
    if (viewerQuery.error && isUnauthorizedMessage(viewerQuery.error.message)) {
      clearAuthSession();
      if (pathname !== "/login") {
        router.replace("/login");
      }
      return;
    }
    if (!viewerQuery.loading && viewerQuery.data && !viewerQuery.data.viewer) {
      clearAuthSession();
      if (pathname !== "/login") {
        router.replace("/login");
      }
    }
  }, [authMode, pathname, router, token, viewerQuery.data, viewerQuery.error, viewerQuery.loading]);

  useEffect(() => {
    if (authMode !== "jwt" || pathname !== "/login") return;
    if (token && viewerQuery.data?.viewer) {
      router.replace("/");
    }
  }, [authMode, pathname, router, token, viewerQuery.data]);

  const value = useMemo<AuthContextValue>(
    () => ({
      authMode,
      authenticated: authMode === "disabled" ? true : Boolean(token && viewerQuery.data?.viewer),
      viewer: viewerQuery.data?.viewer ?? null,
      loading: authMode === "jwt" && hydrated && Boolean(token) && viewerQuery.loading,
      authError: viewerQuery.error?.message ?? null,
      logout: () => {
        clearAuthSession();
        router.replace("/login");
      },
    }),
    [authMode, hydrated, router, token, viewerQuery.data, viewerQuery.error, viewerQuery.loading],
  );

  const shouldBlockProtectedRoute =
    authMode === "jwt" &&
    pathname !== "/login" &&
    (!hydrated || !token || viewerQuery.loading || (viewerQuery.data && !viewerQuery.data.viewer));

  return (
    <AuthContext.Provider value={value}>
      {shouldBlockProtectedRoute ? <AuthLoadingState /> : children}
    </AuthContext.Provider>
  );
}

export function useAuthSession(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthSession must be used within AuthProvider");
  }
  return context;
}
