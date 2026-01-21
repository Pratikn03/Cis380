export default function SettingsPage() {
  return (
    <div className="panel-grid">
      <div>
        <div className="card-title">Settings</div>
        <h1 className="text-3xl mt-3">Environment + Security</h1>
        <p className="muted mt-3">
          Manage tokens, storage endpoints, and observability toggles.
        </p>
      </div>
      <div className="card panel-grid">
        <div>
          <div className="card-title">MLflow</div>
          <p className="muted mt-2">
            Track experiments and artifacts in the MLflow UI.
          </p>
        </div>
        <a
          className="pill-btn"
          href="http://localhost:5000"
          target="_blank"
          rel="noreferrer"
        >
          Open MLflow UI
        </a>
      </div>
    </div>
  );
}
