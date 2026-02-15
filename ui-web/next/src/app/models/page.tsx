"use client";

import { useMemo } from "react";
import { useQuery } from "@apollo/client";
import { OfflineBanner } from "@/components/dashboard/OfflineBanner";
import { MODELS } from "@/lib/gateway-graphql";
import { domainPrimaryMetricPercent, useTrainingReadiness } from "@/lib/hooks/useTrainingReadiness";

type ModelRecord = {
  id: string;
  modelName: string;
  version: string;
  status: string;
  createdAt?: string | null;
};

type ModelsData = {
  models: ModelRecord[];
};

function modelDomainFromName(name: string): string | null {
  const lower = name.toLowerCase();
  if (lower.includes("fraud")) return "fraud";
  if (lower.includes("cyber")) return "cyber";
  if (lower.includes("behavior")) return "behavior";
  if (lower.includes("fusion")) return "fusion";
  if (lower.includes("vision") || lower.includes("voice") || lower.includes("brand")) return "vision";
  return null;
}

function healthTag(status: string): string {
  const low = status.toLowerCase();
  if (low.includes("ready") || low.includes("active") || low.includes("deployed")) return "Ready";
  if (low.includes("fail") || low.includes("error")) return "Needs Attention";
  return "Active";
}

function formatPercent(value: number | null): string {
  return value === null ? "--" : `${value}%`;
}

export default function ModelsPage() {
  const { data, loading, error, refetch } = useQuery<ModelsData>(MODELS, {
    pollInterval: 15000,
  });
  const training = useTrainingReadiness();
  const models = data?.models ?? [];

  const summary = useMemo(() => {
    const active = models.filter((m) => healthTag(m.status) !== "Needs Attention").length;
    const drift = training.domains.filter((domain) => domain.status !== "ready").length;
    return {
      total: models.length,
      active,
      drift,
    };
  }, [models, training.domains]);

  return (
    <div className="sf-page-stack">
      <section className="sf-page-head card">
        <div>
          <h1 className="sf-page-title">Models & Datasets</h1>
          <p className="muted">Model registry, deployment health, and performance telemetry.</p>
        </div>
        <div className="sf-tab-row">
          <button className="sf-tab sf-tab-active" type="button">Home</button>
          <button className="sf-tab" type="button">Models</button>
          <button className="sf-tab" type="button">Market Models</button>
          <button className="sf-tab" type="button">Servers & GPU</button>
        </div>
      </section>

      <section className="sf-metric-mini-row">
        <article className="dash-metric-card metric-teal">
          <div className="dash-metric-label">Total Models</div>
          <div className="dash-metric-value">{summary.total}</div>
          <div className="dash-metric-sub">registry entries</div>
        </article>
        <article className="dash-metric-card metric-purple">
          <div className="dash-metric-label">Healthy</div>
          <div className="dash-metric-value">{summary.active}</div>
          <div className="dash-metric-sub">deployed</div>
        </article>
        <article className="dash-metric-card metric-danger">
          <div className="dash-metric-label">Drift Flags</div>
          <div className="dash-metric-value">{summary.drift}</div>
          <div className="dash-metric-sub">monitoring</div>
        </article>
      </section>

      {training.source === "cache" && (
        <OfflineBanner
          title="Training metrics cached:"
          subtitle={`showing last known model score signals (${training.staleAgeMinutes ?? 0}m stale).`}
        />
      )}
      {training.source === "unavailable" && (
        <OfflineBanner
          title="Training metrics unavailable:"
          subtitle="model score panels will populate after training/readiness artifacts are available."
        />
      )}

      <section className="sf-three-col-cards">
        {models.slice(0, 3).map((model) => {
          const domain = modelDomainFromName(model.modelName);
          const score = domain ? domainPrimaryMetricPercent(training.domainsByKey[domain]) : null;
          return (
            <article key={model.id} className="card sf-compact-card">
              <div className="sf-compact-title">{model.modelName}</div>
              <div className="sf-compact-value">{formatPercent(score)}</div>
              <div className="sf-compact-sub">{model.version}</div>
              <div className="sf-health-chip">{healthTag(model.status)}</div>
            </article>
          );
        })}
        {!models.length && (
          <article className="card sf-compact-card">
            <div className="sf-compact-title">No models available</div>
            <div className="sf-compact-value">--</div>
            <div className="sf-compact-sub">registry empty</div>
            <div className="sf-health-chip">Unavailable</div>
          </article>
        )}
      </section>

      <section className="card table-wrap">
        <div className="sf-panel-headline">
          <div className="sf-panel-heading">Deployed Models</div>
          <button className="pill-btn" onClick={() => refetch()}>
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
        {error && <p className="muted mt-3">Error: {error.message}</p>}
        <table className="table mt-3">
          <thead>
            <tr>
              <th>Name</th>
              <th>Version</th>
              <th>Status</th>
              <th>Created</th>
              <th>Score</th>
            </tr>
          </thead>
          <tbody>
            {models.map((m) => (
              <tr key={m.id}>
                <td>{m.modelName}</td>
                <td>{m.version}</td>
                <td>{m.status}</td>
                <td>{m.createdAt ?? "-"}</td>
                <td>
                  {(() => {
                    const domain = modelDomainFromName(m.modelName);
                    const score = domain ? domainPrimaryMetricPercent(training.domainsByKey[domain]) : null;
                    return formatPercent(score);
                  })()}
                </td>
              </tr>
            ))}
            {!models.length && (
              <tr>
                <td colSpan={5} className="muted">
                  No models found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      <section className="sf-action-strip">
        <button className="sf-strip-btn strip-blue" type="button">Deploy New Model</button>
        <button className="sf-strip-btn strip-purple" type="button">Run Validation</button>
        <button className="sf-strip-btn strip-orange" type="button">Open Drift Report</button>
      </section>
    </div>
  );
}
