"use client";

import { useMutation } from "@apollo/client";
import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { LOGIN } from "@/lib/gateway-graphql";
import { setAuthToken } from "@/lib/auth";
import { authModeLabel, getAuthMode } from "@/lib/runtime";

type LoginPayload = {
  login: {
    accessToken: string | null;
    refreshToken?: string | null;
    tokenType?: string | null;
  } | null;
};

type LoginVariables = {
  username: string;
  password: string;
};

export default function LoginPage() {
  const router = useRouter();
  const authMode = getAuthMode();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [login, { loading }] = useMutation<LoginPayload, LoginVariables>(LOGIN);

  const isJwtMode = authMode === "jwt";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const trimmedUsername = username.trim();
    if (!trimmedUsername || !password.trim()) {
      setError("Username and password are required.");
      return;
    }

    try {
      const response = await login({
        variables: {
          username: trimmedUsername,
          password,
        },
      });
      const token = response.data?.login?.accessToken?.trim();
      if (!token) {
        throw new Error("Login completed without a session token.");
      }

      setAuthToken(token);
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in.");
    }
  }

  if (!isJwtMode) {
    return (
      <div className="sf-page-stack">
        <section className="card panel-grid">
          <div className="card-title">Development Mode</div>
          <h1 className="text-3xl mt-3">Authentication is disabled for this environment</h1>
          <p className="muted mt-3">
            Auth mode is set to {authModeLabel(authMode)}. Production builds clamp this to JWT-only access.
          </p>
        </section>
        <section className="card panel-grid">
          <button className="pill-btn" type="button" onClick={() => router.push("/")}>
            Open Dashboard
          </button>
        </section>
      </div>
    );
  }

  return (
    <div className="sf-page-stack">
      <section className="card panel-grid">
        <div className="card-title">Operator Authentication</div>
        <h1 className="text-3xl mt-3">Sign in with your JWT session</h1>
        <p className="muted mt-3">
          Canonical production access now uses the gateway-backed operator login flow.
        </p>
      </section>

      <section className="card panel-grid">
        <form className="panel-grid" onSubmit={handleSubmit}>
          <label className="panel-grid">
            <span className="card-title">Username</span>
            <input
              className="input"
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="operator"
            />
          </label>
          <label className="panel-grid">
            <span className="card-title">Password</span>
            <input
              className="input"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="••••••••"
            />
          </label>
          {error && <div className="muted">{error}</div>}
          <div className="sf-action-strip">
            <button className="pill-btn" type="submit" disabled={loading}>
              {loading ? "Signing in..." : "Sign in"}
            </button>
            <button className="pill-btn" type="button" onClick={() => router.push("/")}>
              Return to Dashboard
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
