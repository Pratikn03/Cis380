"use client";

import { useQuery } from "@apollo/client";
import { SYSTEM_HEALTH, VIEWER } from "@/lib/gateway-graphql";

export default function AdminPage() {
  const { data: viewerData, loading: loadingViewer, error: viewerError } = useQuery(VIEWER, {
    fetchPolicy: "cache-and-network",
  });
  const { data: healthData, loading: loadingHealth } = useQuery(SYSTEM_HEALTH, {
    pollInterval: 10000,
  });

  const viewer = viewerData?.viewer;
  const roles = Array.isArray(viewer?.roles) ? viewer.roles : [];

  return (
    <div className="sf-page-stack">
      <section className="sf-page-head card">
        <div>
          <h1 className="sf-page-title">Admin & Settings</h1>
          <p className="muted">Security controls, audit workflows, and runtime policy orchestration.</p>
        </div>
        <div className="sf-tab-row">
          <button className="sf-tab sf-tab-active" type="button">Settings</button>
          <button className="sf-tab" type="button">Alerts</button>
          <button className="sf-tab" type="button">Security</button>
          <button className="sf-tab" type="button">Audit View</button>
        </div>
      </section>

      <section className="sf-two-col">
        <article className="card panel-grid">
          <div className="sf-panel-heading">Security</div>
          <div className="sf-mini-kpis">
            <div><span>Alert Threshold</span><strong>0.10</strong></div>
            <div><span>Auto Action</span><strong>Flag</strong></div>
            <div><span>Viewer</span><strong>{loadingViewer ? "loading" : viewer?.username ?? "anon"}</strong></div>
            <div><span>Roles</span><strong>{roles.length || 0}</strong></div>
          </div>
          <div className="sf-role-box">
            <div className="sf-role-title">Role Management</div>
            {roles.length ? (
              roles.map((role: string) => (
                <div key={role} className="sf-role-row">{role}</div>
              ))
            ) : (
              <div className="muted">No roles available.</div>
            )}
          </div>
        </article>

        <article className="card panel-grid">
          <div className="sf-panel-heading">Traffic Firewall</div>
          <div className="sf-mini-kpis">
            <div><span>Status</span><strong>{healthData?.systemHealth?.status ?? "unknown"}</strong></div>
            <div><span>Service</span><strong>{healthData?.systemHealth?.service ?? "gateway"}</strong></div>
            <div><span>Version</span><strong>{healthData?.systemHealth?.version ?? "n/a"}</strong></div>
            <div><span>Uptime</span><strong>{Math.round(healthData?.systemHealth?.uptimeSeconds ?? 0)}s</strong></div>
          </div>
          <div className="sf-log-box">
            <div className="sf-log-row"><span>Rule</span><span>Ingress policy verified</span></div>
            <div className="sf-log-row"><span>Jobs</span><span>Queue integrity stable</span></div>
            <div className="sf-log-row"><span>GraphQL</span><span>Subscription channel healthy</span></div>
          </div>
        </article>
      </section>

      {(viewerError || loadingHealth) && (
        <section className="card">
          <div className="card-title">Diagnostics</div>
          <p className="mt-3 muted">
            {viewerError ? viewerError.message : "Health status refreshing..."}
          </p>
        </section>
      )}

      <section className="sf-action-strip">
        <button className="sf-strip-btn strip-purple" type="button">Start Chat Analysis</button>
        <button className="sf-strip-btn strip-orange" type="button">Movie Recommender</button>
        <button className="sf-strip-btn strip-gold" type="button">Clothes Recommender</button>
      </section>
    </div>
  );
}
