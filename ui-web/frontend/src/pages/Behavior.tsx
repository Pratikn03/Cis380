import { useState, type ChangeEvent } from "react";
import { ErrorState, JsonBlock, MiniBarChart, PageShell, Panel, PrimaryButton } from "../components/DashboardPrimitives";
import { behaviorLogs } from "../services/endpoints";

export default function Behavior() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const leaderboard = result?.top_anomalous || [];

  const onFile = (event: ChangeEvent<HTMLInputElement>) => {
    setFile(event.target.files?.[0] || null);
    event.target.value = "";
  };

  const run = async () => {
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    setError(null);
    try {
      const { data } = await behaviorLogs(form);
      setResult(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  return (
    <PageShell title="Behavior" eyebrow="Insider Risk">
      <div className="grid gap-4 lg:grid-cols-[24rem_1fr]">
        <Panel title="Behavior Log CSV">
          <input
            type="file"
            accept=".csv,text/csv"
            aria-label="Upload behavior CSV"
            onChange={onFile}
            className="text-sm"
          />
          <PrimaryButton onClick={run} disabled={!file} className="mt-3">
            Score Users
          </PrimaryButton>
          <ErrorState message={error} />
          {result?.summary?.degraded && <p className="mt-3 text-sm text-amber-700">Model unavailable; heuristic scoring is active.</p>}
        </Panel>
        <Panel title="Insider Risk Leaderboard">
          <MiniBarChart
            data={leaderboard.map((row: any) => ({
              label: row.user_id || "all users",
              value: Number(row.anomaly_score || 0),
            }))}
          />
        </Panel>
      </div>
      <Panel title="Sequence Visualization" className="mt-4">
        <JsonBlock value={result || { top_anomalous: [] }} />
      </Panel>
    </PageShell>
  );
}
