import SectionHeader from "../components/SectionHeader";
import { runbooks } from "../data/operations";

export default function Operations() {
  return (
    <main className="section-shell mt-10 pb-12">
      <SectionHeader
        eyebrow="Operations"
        title="Local-first runbooks with production-grade hygiene"
        description="Start locally, publish to GitHub Pages, and keep the Streamlit UI as a backup interface when needed."
      />

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {runbooks.map((runbook) => (
          <div key={runbook.title} className="card-panel px-6 py-6">
            <h3 className="text-lg font-display font-semibold">{runbook.title}</h3>
            <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-fog">
              {runbook.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="mt-12 grid gap-6 lg:grid-cols-2">
        <div className="card-panel px-6 py-6">
          <h3 className="text-lg font-display font-semibold">Environment settings</h3>
          <p className="mt-3 text-sm text-fog">
            Configure the UI with environment variables so it can point to your live backend.
          </p>
          <pre className="mt-4 rounded-xl bg-slate-900 p-4 text-xs text-slate-100">
            {`VITE_API_BASE=http://localhost:8000\nVITE_BASE_PATH=/`}
          </pre>
        </div>

        <div className="card-panel px-6 py-6">
          <h3 className="text-lg font-display font-semibold">Release checklist</h3>
          <ul className="mt-4 space-y-2 text-sm text-fog">
            <li>Run API health checks and confirm /api/risk/analyze responses.</li>
            <li>Validate model weights are loaded (vision, voice, fraud).</li>
            <li>Confirm UI build uses correct base path for GitHub Pages.</li>
            <li>Keep Streamlit as a backup route in case the web UI is offline.</li>
          </ul>
        </div>
      </div>
    </main>
  );
}
