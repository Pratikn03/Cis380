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
      <div className="card">Add RBAC + secrets configuration here.</div>
    </div>
  );
}
