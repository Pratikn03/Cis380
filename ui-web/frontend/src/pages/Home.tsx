import { Link } from "react-router-dom";
import SectionHeader from "../components/SectionHeader";
import StatCard from "../components/StatCard";
import CapabilityCard from "../components/CapabilityCard";
import { showcaseMetrics } from "../data/metrics";
import { capabilityCards } from "../data/capabilities";

export default function Home() {
  return (
    <main>
      <section className="section-shell pt-10">
        <div className="hero-skyline relative overflow-hidden px-10 py-12 animate-rise">
          <div className="relative z-10 max-w-3xl">
            <p className="text-xs uppercase tracking-[0.4em] text-amber-200">
              Production Web UI
            </p>
            <h1 className="mt-4 text-4xl font-display font-semibold">
              SentinelForge Command Center
            </h1>
            <p className="mt-4 text-base text-slate-200">
              A production-grade platform that unifies risk intelligence, multimodal inference,
              and monitoring into one operational surface. Built to be API-first and audit-ready.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                to="/command"
                className="rounded-full bg-emerald-500 px-5 py-2 text-sm font-semibold text-slate-900"
              >
                Open Live Console
              </Link>
              <Link
                to="/architecture"
                className="rounded-full border border-slate-500 px-5 py-2 text-sm font-semibold text-slate-100"
              >
                View Architecture
              </Link>
            </div>
          </div>
          <div className="relative z-10 mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {showcaseMetrics.map((metric, index) => (
              <div
                key={metric.label}
                className="glass-panel px-4 py-3 animate-rise"
                style={{ animationDelay: `${0.15 * index}s` }}
              >
                <p className="text-xs uppercase tracking-[0.25em] text-emerald-200">
                  {metric.label}
                </p>
                <p className="mt-2 text-lg font-display font-semibold text-white">
                  {metric.value}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section-shell mt-14">
        <SectionHeader
          eyebrow="Capability Grid"
          title="What the platform delivers"
          description="SentinelForge routes requests to the right intelligence module and returns a single structured answer with full traceability."
        />
        <div className="grid gap-6 md:grid-cols-2">
          {capabilityCards.map((card) => (
            <CapabilityCard key={card.title} {...card} />
          ))}
        </div>
      </section>

      <section className="section-shell mt-14">
        <SectionHeader
          eyebrow="Operational Footprint"
          title="Prepared for production operations"
          description="Designed to run locally or in production, with deterministic fallbacks and explicit artifact checks."
        />
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <StatCard label="API Gateway" value="FastAPI" />
          <StatCard label="Monitoring" value="JSONL + Prometheus" />
          <StatCard label="Model Store" value="Local weights" />
          <StatCard label="Deployment" value="Docker or Local" />
        </div>
      </section>

      <section className="section-shell mt-14">
        <SectionHeader
          eyebrow="Skill Stack"
          title="Engineering focus"
          description="Showcase-ready technologies and systems thinking aligned to modern product delivery."
        />
        <div className="grid gap-4 md:grid-cols-2">
          <div className="card-panel px-6 py-6">
            <h3 className="text-lg font-display font-semibold">Frontend</h3>
            <p className="mt-2 text-sm text-fog">
              React, TypeScript, Tailwind CSS, routing, and component architecture.
            </p>
          </div>
          <div className="card-panel px-6 py-6">
            <h3 className="text-lg font-display font-semibold">Backend and Systems</h3>
            <p className="mt-2 text-sm text-fog">
              FastAPI, Python, model pipelines, data structures, and systems-level design principles.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
