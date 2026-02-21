export default function Home() {
  return (
    <main className="p-6 md:p-10">
      <header className="rounded-2xl border border-slate-700 bg-slate-900/60 p-6">
        <h1 className="text-2xl font-semibold text-white">Sentifargo Dashboard</h1>
        <p className="mt-2 text-sm text-slate-400">
          Unified monitoring for fraud, cyber, behavior, vision, voice, and recommendation systems.
        </p>
      </header>

      <section className="mt-6 grid gap-4 md:grid-cols-3">
        <article className="rounded-xl border border-slate-700 bg-slate-900/50 p-4">
          <h2 className="text-sm font-medium text-slate-200">Model Readiness</h2>
          <p className="mt-2 text-xs text-slate-400">
            Use the command center to review training readiness and blockers across all domains.
          </p>
        </article>
        <article className="rounded-xl border border-slate-700 bg-slate-900/50 p-4">
          <h2 className="text-sm font-medium text-slate-200">Risk Monitoring</h2>
          <p className="mt-2 text-xs text-slate-400">
            Track `risk_summary`, drift trends, and latest event decisions in near real-time.
          </p>
        </article>
        <article className="rounded-xl border border-slate-700 bg-slate-900/50 p-4">
          <h2 className="text-sm font-medium text-slate-200">Auth & Access</h2>
          <p className="mt-2 text-xs text-slate-400">
            Sign in from the sidebar to unlock protected API flows and dashboard integrations.
          </p>
        </article>
      </section>
    </main>
  );
}
