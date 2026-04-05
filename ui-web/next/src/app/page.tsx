"use client";

import { useState } from "react";
import Link from "next/link";
import { AlertFeed } from "@/components/dashboard/AlertFeed";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { MediaInsightTile, type MediaInsight } from "@/components/dashboard/MediaInsightTile";
import { OfflineBanner } from "@/components/dashboard/OfflineBanner";
import { QuickActionGrid } from "@/components/dashboard/QuickActionGrid";
import { SignalChart } from "@/components/dashboard/SignalChart";
import { TrainingReadinessStrip } from "@/components/dashboard/TrainingReadinessStrip";
import { RecommenderPanel } from "@/components/recommend/RecommenderPanel";
import { useDashboardSummary } from "@/lib/hooks/useDashboardSummary";
import { useTrainingReadiness } from "@/lib/hooks/useTrainingReadiness";

function formatUptime(seconds: number | null | undefined): string {
  if (!Number.isFinite(seconds ?? NaN) || (seconds ?? 0) < 0) return "n/a";
  const total = Math.floor(seconds as number);
  const days = Math.floor(total / 86400);
  const hours = Math.floor((total % 86400) / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

function formatMetric(value: number | null | undefined): string {
  if (typeof value !== "number" || Number.isNaN(value)) return "--";
  return String(value);
}

export default function DashboardPage() {
  const {
    fraudAlerts,
    docsIndexed,
    activeJobs,
    riskScore,
    healthStatus,
    gatewayService,
    uptimeSeconds,
    alertFeed,
    streamAlert,
    gatewayOffline,
    source: dashboardSource,
    staleAgeMinutes: dashboardStaleAgeMinutes,
    refetch: refreshDashboard,
  } = useDashboardSummary();
  const training = useTrainingReadiness();
  const [refreshTarget, setRefreshTarget] = useState<"dashboard" | "training" | "all" | null>(null);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [lastManualRefresh, setLastManualRefresh] = useState<string | null>(null);

  const refreshDashboardOnly = refreshTarget === "dashboard" || refreshTarget === "all";
  const refreshTrainingOnly = refreshTarget === "training" || refreshTarget === "all";

  const runRefresh = async (target: "dashboard" | "training" | "all") => {
    setRefreshTarget(target);
    setRefreshError(null);
    try {
      if (target === "dashboard") {
        await refreshDashboard();
      } else if (target === "training") {
        await training.refetch();
      } else {
        await Promise.all([refreshDashboard(), training.refetch()]);
      }
      setLastManualRefresh(new Date().toLocaleTimeString());
    } catch (error: unknown) {
      setRefreshError(error instanceof Error ? error.message : String(error));
    } finally {
      setRefreshTarget(null);
    }
  };

  const mediaCards: MediaInsight[] = [
    {
      title: "Video Emotion Analysis",
      tag: activeJobs > 0 ? "Processing" : "Ready",
      tone: "video",
    },
    {
      title: "Deepfake Detection",
      tag: fraudAlerts > 0 ? "Investigate" : "Monitoring",
      tone: "deepfake",
    },
    {
      title: "Brand Logo Identified",
      tag: docsIndexed > 0 ? "Catalog Linked" : "No Samples",
      tone: "brand",
    },
    {
      title: "Voice Emotion",
      tag: gatewayOffline ? "Offline" : "Confident",
      tone: "voice",
    },
  ];

  const feed = streamAlert ? [streamAlert, ...alertFeed].slice(0, 6) : alertFeed;

  return (
    <div className="dash-page">
      {dashboardSource === "cache" && (
        <OfflineBanner
          title="Gateway data cached:"
          subtitle={`showing last known real values (${dashboardStaleAgeMinutes ?? 0}m stale).`}
        />
      )}

      {dashboardSource === "unavailable" && (
        <OfflineBanner
          title="Gateway unavailable:"
          subtitle="live dashboard metrics are unavailable until API reconnects."
        />
      )}

      {training.source === "cache" && (
        <OfflineBanner
          title="Training data cached:"
          subtitle={`showing last known training readiness (${training.staleAgeMinutes ?? 0}m stale).`}
        />
      )}

      {training.source === "unavailable" && (
        <OfflineBanner
          title="Training data unavailable:"
          subtitle="no cached readiness snapshot found yet."
        />
      )}

      <section className="dash-metric-row">
        <KpiCard label="Fraud Alerts" value={formatMetric(fraudAlerts)} subLabel="active" tone="danger" />
        <KpiCard label="Document Indexing" value={formatMetric(docsIndexed)} subLabel="chunks" tone="teal" />
        <KpiCard label="Jobs In Progress" value={formatMetric(activeJobs)} subLabel="running" tone="purple" />
      </section>

      <TrainingReadinessStrip
        domains={training.domains}
        readyCount={training.readyCount}
        totalCount={training.totalCount}
        generatedAt={training.generatedAt}
        source={training.source}
        staleAgeMinutes={training.staleAgeMinutes}
        hasBlockers={training.hasBlockers}
        onRefresh={() => runRefresh("training")}
        refreshing={refreshTrainingOnly}
      />

      <section className="dash-main-grid">
        <article className="card dash-system-panel">
          <div className="dash-panel-title">System Activity</div>
          <div className="dash-mini-charts">
            <div className="dash-chart-box">
              <div className="dash-chart-title">API Requests</div>
              <SignalChart kind="line" />
            </div>
            <div className="dash-chart-box">
              <div className="dash-chart-title">Alerts</div>
              <SignalChart kind="bars" />
            </div>
          </div>
          <div className="dash-job-box">
            <div className="dash-chart-title">Job Status</div>
            <SignalChart kind="bars" />
          </div>
        </article>

        <article className="card dash-media-panel">
          <div className="dash-panel-title">Live Media Analysis</div>
          <div className="dash-media-grid">
            {mediaCards.map((item) => (
              <MediaInsightTile key={item.title} item={item} />
            ))}
          </div>
        </article>

        <aside className="card dash-actions-panel">
          <div className="dash-panel-headline">
            <div className="dash-panel-title">Quick Actions</div>
            <button className="pill-btn" type="button" onClick={() => void runRefresh("dashboard")} disabled={refreshDashboardOnly}>
              {refreshDashboardOnly ? "Refreshing dashboard..." : "Refresh Dashboard"}
            </button>
          </div>
          <p className="dash-control-copy">
            {refreshError
              ? `Refresh failed: ${refreshError}`
              : lastManualRefresh
                ? `Last manual refresh at ${lastManualRefresh}.`
                : "Pull the latest gateway metrics and readiness signals without leaving the home view."}
          </p>
          <QuickActionGrid
            actions={[
              { href: "/risk", label: "Run Risk Analysis", tone: "amber" },
              { href: "/jobs", label: "Inspect Active Jobs", tone: "cyan" },
              { href: "/models", label: "Review Model Health", tone: "pink" },
              { href: "/rag", label: "Run RAG Query", tone: "blue" },
            ]}
          />
        </aside>
      </section>

      <section className="dash-bottom-grid">
        <article className="card">
          <div className="dash-panel-title">Alerts & Insights</div>
          <AlertFeed items={feed.length ? feed : [{ level: "info", message: "Signal bus idle", timestamp: new Date().toISOString() }]} />
        </article>

        <article className="dash-action-strip">
          <Link href="/rag" className="dash-strip-btn strip-purple">
            Start Chat Analysis
          </Link>
          <Link href="/models" className="dash-strip-btn strip-orange">
            Open Model Registry
          </Link>
          <Link href="/datasets" className="dash-strip-btn strip-gold">
            Open Dataset Catalog
          </Link>
          <Link href="/live-media" className="dash-strip-btn strip-blue">
            Analyze Video
          </Link>
        </article>
      </section>

      <section className="dash-footer-kpis">
        <div>
          <span>Health</span>
          <strong>{healthStatus ?? "--"}</strong>
        </div>
        <div>
          <span>Uptime</span>
          <strong>{formatUptime(uptimeSeconds)}</strong>
        </div>
        <div>
          <span>Risk Score</span>
          <strong>{typeof riskScore === "number" ? `${riskScore}%` : "--"}</strong>
        </div>
        <div>
          <span>Active Jobs</span>
          <strong>{formatMetric(activeJobs)}</strong>
        </div>
        <div>
          <span>Gateway</span>
          <strong>{gatewayService ?? "--"}</strong>
        </div>
      </section>

      <RecommenderPanel />
    </div>
  );
}
