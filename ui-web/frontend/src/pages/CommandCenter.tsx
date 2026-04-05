const stats = [
  { label: "Images Processed", value: "154K+" },
  { label: "ML Models", value: "6" },
  { label: "Detection Accuracy", value: "99.2%" },
  { label: "API Endpoints", value: "15+" },
];

const capabilities = [
  {
    title: "Fraud Detection",
    details: "Transaction scoring with real-time anomaly signals and explainable outputs.",
  },
  {
    title: "Cybersecurity",
    details: "Network intrusion detection and pattern-based threat analysis.",
  },
  {
    title: "Behavior Analytics",
    details: "User behavior modeling for insider threat detection and anomaly scoring.",
  },
  {
    title: "Vision Intelligence",
    details: "Image authenticity checks, face emotion inference, and brand/logo detection.",
  },
  {
    title: "Voice Emotion",
    details: "Audio emotion recognition with offline-first inference.",
  },
  {
    title: "RAG + Recommendations",
    details: "Document Q&A and personalized recommendations with local embeddings.",
  },
];

const quickStart = [
  {
    label: "Run the canonical API",
    command: "uvicorn app.main:app --reload --port 8000",
  },
  {
    label: "Run the compatibility UI",
    command: "cd ui-web/frontend && npm install && npm run dev",
  },
  {
    label: "Run Streamlit Command Center",
    command: "streamlit run app/streamlit_chatbot/app.py",
  },
];

const projectSummary = `Legacy compatibility snapshot

This UI is preserved for rollback, reference, and compatibility testing.
The canonical product path is Next + Kotlin GraphQL + FastAPI.

What it still shows:
- Historical multimodal workflows for fraud, cyber, behavior, vision, voice, and recommendations
- Local API wiring and preview-era routing
- Archived operational context from the migration period

How to use it:
- Validate only when legacy files change or when explicitly requested
- Treat the content as historical context, not release truth
`;

export default function CommandCenter() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-6xl mx-auto space-y-10">
        <section className="space-y-4">
          <p className="text-sm uppercase tracking-[0.3em] text-emerald-400">
            Sentifargo
          </p>
          <h1 className="text-4xl md:text-5xl font-bold text-white">Sentifargo</h1>
          <p className="text-slate-300 max-w-3xl">
            A legacy compatibility surface for fraud detection, cybersecurity monitoring,
            behavioral analytics, and vision intelligence. The canonical runtime now lives in
            Next, Kotlin GraphQL, and FastAPI.
          </p>
          <div className="flex flex-wrap gap-3">
            <a
              href="https://pratikn03.github.io/Cis380/"
              target="_blank"
              rel="noreferrer"
              className="px-5 py-2 bg-emerald-500 text-slate-900 font-semibold rounded-lg hover:bg-emerald-400 transition-colors"
            >
              Compatibility Preview
            </a>
            <a
              href="https://github.com/Pratikn03/Cis380"
              target="_blank"
              rel="noreferrer"
              className="px-5 py-2 border border-slate-600 text-slate-200 rounded-lg hover:border-emerald-400 transition-colors"
            >
              GitHub Repo
            </a>
          </div>
        </section>

        <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-xl border border-slate-700 bg-slate-800/50 p-4"
            >
              <p className="text-xs text-slate-400">{stat.label}</p>
              <p className="text-2xl font-semibold text-emerald-300">{stat.value}</p>
            </div>
          ))}
        </section>

        <section className="space-y-4">
          <div>
            <h2 className="text-2xl font-semibold text-white">Core Capabilities</h2>
            <p className="text-slate-400">
              Historical capability map retained for compatibility and rollback reference.
            </p>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            {capabilities.map((capability) => (
              <div
                key={capability.title}
                className="rounded-xl border border-slate-700 bg-slate-800/50 p-5"
              >
                <p className="text-lg font-semibold text-white">{capability.title}</p>
                <p className="text-sm text-slate-400 mt-2">{capability.details}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="space-y-4">
          <div>
            <h2 className="text-2xl font-semibold text-white">Quick Start</h2>
            <p className="text-slate-400">
              Run the backend and compatibility UI locally, then inspect the archived flows.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-4">
            {quickStart.map((item) => (
              <div
                key={item.label}
                className="rounded-xl border border-slate-700 bg-slate-900/70 p-4"
              >
                <p className="text-sm font-semibold text-emerald-300">{item.label}</p>
                <pre className="mt-3 text-xs text-slate-300 whitespace-pre-wrap break-words">
                  {item.command}
                </pre>
              </div>
            ))}
          </div>
        </section>

        <section className="space-y-4">
          <div>
            <h2 className="text-2xl font-semibold text-white">Project Summary</h2>
            <p className="text-slate-400">
              Historical project overview kept for reference during migration.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-700 bg-slate-900/60 p-6">
            <pre className="text-xs text-slate-300 whitespace-pre-wrap">
              {projectSummary}
            </pre>
          </div>
        </section>
      </div>
    </main>
  );
}
