"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const refresh = () => {
    setLoading(true);
    apiFetch<any[]>("/api/v1/jobs?limit=50")
      .then((data) => setJobs(data))
      .catch((err) => setError(String(err.message || err)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    refresh();
  }, []);

  const startRagIndex = async () => {
    setError("");
    await apiFetch("/api/v1/jobs/start", {
      method: "POST",
      body: JSON.stringify({ type: "rag_index", payload: {} }),
    }).catch((err) => setError(String(err.message || err)));
    refresh();
  };

  return (
    <div className="panel-grid">
      <div>
        <div className="card-title">Ops</div>
        <h1 className="text-3xl mt-3">Job Control Plane</h1>
        <p className="muted mt-3">
          Start background tasks and track progress across ingestion, training, and scoring.
        </p>
      </div>
      <div className="flex flex-wrap gap-3">
        <button className="pill-btn" onClick={startRagIndex}>
          Start RAG Index
        </button>
        <button className="pill-btn" onClick={refresh}>
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>
      {error && <div className="card">Error: {error}</div>}
      <div className="card">
        <div className="card-title">Recent Jobs</div>
        <div className="table-wrap mt-4">
          <table className="table">
            <thead>
              <tr>
                <th>Job</th>
                <th>Type</th>
                <th>Status</th>
                <th>Progress</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.job_id}>
                  <td className="font-mono">{String(job.job_id).slice(0, 8)}…</td>
                  <td>{job.type}</td>
                  <td>{job.status}</td>
                  <td>{Math.round((job.progress || 0) * 100)}%</td>
                  <td>{job.message}</td>
                </tr>
              ))}
              {!jobs.length && (
                <tr>
                  <td colSpan={5} className="muted">
                    No jobs yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
