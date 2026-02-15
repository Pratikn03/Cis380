"use client";

import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();

  return (
    <div className="panel-grid">
      <div>
        <div className="card-title">Authentication Disabled</div>
        <h1 className="text-3xl mt-3">No Login Required</h1>
        <p className="muted mt-3">This environment is configured to allow direct dashboard access.</p>
      </div>
      <div className="card panel-grid">
        <button className="pill-btn" onClick={() => router.push("/")}>
          Open Dashboard
        </button>
      </div>
    </div>
  );
}
