export default function SettingsPage() {
  const graphqlHttp = process.env.NEXT_PUBLIC_GRAPHQL_HTTP ?? "http://localhost:8081/graphql";
  const graphqlWs = process.env.NEXT_PUBLIC_GRAPHQL_WS ?? "ws://localhost:8081/graphql";

  return (
    <div className="sf-page-stack">
      <section className="sf-page-head card">
        <div>
          <h1 className="sf-page-title">Environment + Security</h1>
          <p className="muted">
            Gateway endpoint controls, policy toggles, and observability quick links.
          </p>
        </div>
        <div className="sf-tab-row">
          <button className="sf-tab sf-tab-active" type="button">
            Settings
          </button>
          <button className="sf-tab" type="button">
            Runtime
          </button>
          <button className="sf-tab" type="button">
            Observability
          </button>
        </div>
      </section>

      <section className="sf-two-col">
        <article className="card panel-grid">
          <div className="sf-panel-heading">GraphQL Endpoints</div>
          <div className="sf-endpoint-box">
            <span>GraphQL HTTP</span>
            <code>{graphqlHttp}</code>
          </div>
          <div className="sf-endpoint-box">
            <span>GraphQL WS</span>
            <code>{graphqlWs}</code>
          </div>
          <div className="sf-mini-kpis">
            <div>
              <span>Auth Mode</span>
              <strong>Open Access</strong>
            </div>
            <div>
              <span>Subscriptions</span>
              <strong>Enabled</strong>
            </div>
            <div>
              <span>Cache</span>
              <strong>Apollo Memory</strong>
            </div>
            <div>
              <span>Transport</span>
              <strong>HTTP + WS</strong>
            </div>
          </div>
        </article>

        <article className="card panel-grid">
          <div className="sf-panel-heading">Tools + External Services</div>
          <a
            className="pill-btn rounded-xl bg-gradient-to-r from-cyan-500/20 to-blue-500/20"
            href="http://localhost:5000"
            target="_blank"
            rel="noreferrer"
          >
            Open MLflow UI
          </a>
          <button
            className="pill-btn rounded-xl bg-gradient-to-r from-indigo-500/20 to-violet-500/20"
            type="button"
          >
            Open Gateway Health
          </button>
          <button
            className="pill-btn rounded-xl bg-gradient-to-r from-amber-500/20 to-orange-500/20"
            type="button"
          >
            Open API Health
          </button>
          <div className="sf-log-box">
            <div className="sf-log-row">
              <span>Audit</span>
              <span>Config snapshot synced</span>
            </div>
            <div className="sf-log-row">
              <span>TLS</span>
              <span>Dev cert profile active</span>
            </div>
            <div className="sf-log-row">
              <span>Rate Limits</span>
              <span>Policy set: standard</span>
            </div>
          </div>
        </article>
      </section>

      <section className="sf-action-strip">
        <button className="sf-strip-btn strip-blue" type="button">
          Save Runtime Profile
        </button>
        <button className="sf-strip-btn strip-purple" type="button">
          Export Config
        </button>
        <button className="sf-strip-btn strip-orange" type="button">
          Run Connectivity Check
        </button>
      </section>
    </div>
  );
}
