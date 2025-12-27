import SectionHeader from "../components/SectionHeader";
import { architectureLayers } from "../data/architecture";

const dataFlow = [
  {
    title: "Ingress",
    detail: "Web UI and Streamlit issue requests to FastAPI endpoints with structured payloads.",
  },
  {
    title: "Policy",
    detail: "Risk policies validate device, country, and behavior signals before model routing.",
  },
  {
    title: "Inference",
    detail: "Vision, voice, and fraud engines run locally with artifact checks and fallbacks.",
  },
  {
    title: "Audit",
    detail: "Every decision is logged to JSONL for replay and monitoring dashboards.",
  },
];

const artifactChecklist = [
  "models/vision/face_emotion/model.pt",
  "models/vision/face_emotion/classes.txt",
  "models/brand (YOLO weights)",
  "data/processed assets for recommenders",
  "runs/mlflow or monitoring logs",
];

export default function Architecture() {
  return (
    <main className="section-shell mt-10 pb-12">
      <SectionHeader
        eyebrow="Architecture"
        title="Layered system designed for real operations"
        description="SentinelForge isolates interface, orchestration, model engines, and monitoring so deployments stay resilient and auditable."
      />

      <div className="grid gap-6 md:grid-cols-2">
        {architectureLayers.map((layer, index) => (
          <div key={layer.title} className="card-panel px-6 py-6">
            <p className="text-xs uppercase tracking-[0.25em] text-moss">Layer {index + 1}</p>
            <h3 className="mt-3 text-xl font-display font-semibold text-ink">{layer.title}</h3>
            <p className="mt-2 text-sm text-fog">{layer.description}</p>
          </div>
        ))}
      </div>

      <div className="mt-12 grid gap-6 lg:grid-cols-3">
        <div className="card-panel px-6 py-6">
          <h3 className="text-lg font-display font-semibold">Data flow</h3>
          <div className="mt-4 space-y-3">
            {dataFlow.map((flow) => (
              <div key={flow.title}>
                <p className="text-sm font-semibold text-ink">{flow.title}</p>
                <p className="text-sm text-fog">{flow.detail}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="card-panel px-6 py-6">
          <h3 className="text-lg font-display font-semibold">Artifact readiness</h3>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-fog">
            {artifactChecklist.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="card-panel px-6 py-6">
          <h3 className="text-lg font-display font-semibold">API surface</h3>
          <ul className="mt-4 space-y-2 text-sm text-fog">
            <li>POST /api/chat</li>
            <li>POST /api/chat/multimodal</li>
            <li>POST /api/risk/analyze</li>
            <li>POST /api/vision/brand/predict</li>
            <li>POST /api/voice/emotion</li>
          </ul>
          <p className="mt-3 text-xs text-fog">
            These endpoints power the Command Center and the Streamlit fallback UI.
          </p>
        </div>
      </div>
    </main>
  );
}
