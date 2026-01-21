"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

export default function DashboardPage() {
  const [health, setHealth] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let active = true;
    Promise.all([apiFetch("/api/health"), apiFetch("/api/monitor/summary")])
      .then(([healthData, summaryData]) => {
        if (!active) return;
        setHealth(healthData);
        setSummary(summaryData);
      })
      .catch((err) => {
        if (!active) return;
        setError(String(err.message || err));
      });
    return () => {
      active = false;
    };
  }, []);

  if (error) {
    return (
      <div className="panel-grid">
        <h1 className="text-2xl">Dashboard</h1>
        <div className="card">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="panel-grid">
      <div>
        <div className="card-title">System Snapshot</div>
        <h1 className="text-3xl mt-3">Command Center Overview</h1>
        <p className="muted mt-3">
          Live health + monitoring signals from your core API services.
        </p>
      </div>
      <div className="panel-grid lg:grid-cols-2">
        <div className="card">
          <div className="card-title">Health</div>
          <pre className="mt-3 whitespace-pre-wrap text-sm">
            {health ? JSON.stringify(health, null, 2) : "Loading..."}
          </pre>
        </div>
        <div className="card">
          <div className="card-title">Monitor Summary</div>
          <pre className="mt-3 whitespace-pre-wrap text-sm">
            {summary ? JSON.stringify(summary, null, 2) : "Loading..."}
          </pre>
        </div>
      </div>
    </div>
  );
}
