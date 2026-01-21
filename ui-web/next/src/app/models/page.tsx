export default function ModelsPage() {
  return (
    <div className="panel-grid">
      <div>
        <div className="card-title">Model Registry</div>
        <h1 className="text-3xl mt-3">Versions + Metrics</h1>
        <p className="muted mt-3">
          Track model lineage, performance, drift, and promotion gates.
        </p>
      </div>
      <div className="card">Wire to /api/v1/models for live model metadata.</div>
    </div>
  );
}
