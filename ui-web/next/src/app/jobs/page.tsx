"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useSubscription } from "@apollo/client";
import { JOB_PROGRESS, JOBS, START_JOB } from "@/lib/gateway-graphql";
import { OfflineBanner } from "@/components/dashboard/OfflineBanner";

type JobRecord = {
  jobId: string;
  taskId?: string | null;
  type: string;
  status: string;
  progress: number;
  message: string;
  createdAt?: string | null;
};

export default function JobsPage() {
  const [error, setError] = useState("");
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  const { data, loading, error: queryError, refetch } = useQuery(JOBS, {
    variables: { limit: 50 },
    pollInterval: 8000,
  });

  const [startJob, { loading: starting }] = useMutation(START_JOB);

  const jobs: JobRecord[] = useMemo(() => data?.jobs ?? [], [data]);
  const activeJobId = selectedJobId ?? jobs[0]?.jobId ?? null;

  const { data: progressData } = useSubscription(JOB_PROGRESS, {
    skip: !activeJobId,
    variables: { jobId: activeJobId },
  });

  const liveProgress = progressData?.jobProgress;

  const onStartRagIndex = async () => {
    setError("");
    try {
      const out = await startJob({
        variables: {
          input: {
            type: "rag_index",
            rebuild: false,
          },
        },
      });
      const id = out.data?.startJob?.jobId;
      if (id) setSelectedJobId(id);
      await refetch();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const offline = Boolean(queryError);

  return (
    <div className="sf-page-stack">
      <section className="sf-page-head card">
        <div>
          <h1 className="sf-page-title">Ops Center</h1>
          <p className="muted">Background jobs, worker progress, and orchestration telemetry.</p>
        </div>
        <div className="sf-tab-row">
          <button className="sf-tab sf-tab-active" type="button">Jobs</button>
          <button className="sf-tab" type="button">Workers</button>
          <button className="sf-tab" type="button">History</button>
        </div>
      </section>

      {offline && (
        <OfflineBanner title="Jobs API unavailable:" subtitle="showing cached rows while gateway reconnects." />
      )}

      <section className="card panel-grid">
        <div className="flex flex-wrap gap-3">
          <button className="pill-btn" onClick={onStartRagIndex}>
            {starting ? "Starting..." : "Start RAG Index"}
          </button>
          <button className="pill-btn" onClick={() => refetch()}>
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
        {error && <div className="muted">Error: {error}</div>}
      </section>

      <section className="sf-two-col">
        <article className="card">
          <div className="card-title">Live Progress</div>
          <pre className="sf-pretty-pre mt-3">
            {liveProgress ? JSON.stringify(liveProgress, null, 2) : "Waiting for subscription..."}
          </pre>
        </article>

        <article className="card">
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
                  <tr key={job.jobId} onClick={() => setSelectedJobId(job.jobId)}>
                    <td className="font-mono">{String(job.jobId).slice(0, 8)}…</td>
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
        </article>
      </section>
    </div>
  );
}
