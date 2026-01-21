"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  const login = async () => {
    setMessage("");
    try {
      const res = await apiFetch<{ access_token: string }>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      localStorage.setItem("AUTH_TOKEN", res.access_token);
      setMessage("Token saved. You can now access protected routes.");
    } catch (err: any) {
      setMessage(String(err.message || err));
    }
  };

  return (
    <div className="panel-grid">
      <div>
        <div className="card-title">Authentication</div>
        <h1 className="text-3xl mt-3">Login</h1>
        <p className="muted mt-3">Use your admin credentials to access protected APIs.</p>
      </div>
      <div className="card panel-grid">
        <input
          className="input"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
        />
        <input
          className="input"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
        />
        <button className="pill-btn" onClick={login}>
          Login
        </button>
        {message && <div className="muted">{message}</div>}
      </div>
    </div>
  );
}
