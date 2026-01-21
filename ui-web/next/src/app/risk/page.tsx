export default function RiskPage() {
  return (
    <div className="panel-grid">
      <div>
        <div className="card-title">Risk Console</div>
        <h1 className="text-3xl mt-3">Fraud + Cyber + Behavior</h1>
        <p className="muted mt-3">
          Configure alert thresholds, view evidence, and track fusion risk scores.
        </p>
      </div>
      <div className="card">Connect this page to /api/risk and monitoring streams.</div>
    </div>
  );
}
