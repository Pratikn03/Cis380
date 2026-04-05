export default function Home() {
  return (
    <main className="p-6 md:p-10">
      <header className="rounded-2xl border border-slate-700 bg-slate-900/60 p-6">
        <h1 className="text-2xl font-semibold text-white">Sentifargo Legacy Compatibility</h1>
        <p className="mt-2 text-sm text-slate-400">
          Compatibility-only dashboard for fraud, cyber, behavior, vision, voice, and recommendation workflows.
        </p>
      </header>

      <section className="mt-6 grid gap-4 md:grid-cols-3">
        <article className="rounded-xl border border-slate-700 bg-slate-900/50 p-4">
          <h2 className="text-sm font-medium text-slate-200">Historical Model Readiness</h2>
          <p className="mt-2 text-xs text-slate-400">
            Use the legacy UI to inspect archived readiness signals and rollback context.
          </p>
        </article>
        <article className="rounded-xl border border-slate-700 bg-slate-900/50 p-4">
          <h2 className="text-sm font-medium text-slate-200">Risk Monitoring</h2>
          <p className="mt-2 text-xs text-slate-400">
            Track `risk_summary`, drift trends, and historical event decisions in near real-time.
          </p>
        </article>
        <article className="rounded-xl border border-slate-700 bg-slate-900/50 p-4">
          <h2 className="text-sm font-medium text-slate-200">Compatibility Access</h2>
          <p className="mt-2 text-xs text-slate-400">
            Sign in from the sidebar to inspect legacy API flows and compatibility integrations.
          </p>
        </article>
      </section>
    </main>
  );
}
