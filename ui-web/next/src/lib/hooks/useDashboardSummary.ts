"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery, useSubscription } from "@apollo/client";
import { DASHBOARD_SUMMARY, JOBS, RAG_STATUS, SYSTEM_ALERTS, SYSTEM_HEALTH } from "@/lib/gateway-graphql";

const DASHBOARD_CACHE_KEY = "sf:last_dashboard_summary";

export type AlertRecord = {
  level?: string | null;
  message?: string | null;
  component?: string | null;
  timestamp?: string | null;
};

type SummarySnapshot = {
  fraudAlerts: number | null;
  docsIndexed: number | null;
  activeJobs: number | null;
  riskScore: number | null;
  healthStatus: string | null;
  gatewayService: string | null;
  uptimeSeconds: number | null;
  alertFeed: AlertRecord[];
};

type CachedSummary = {
  cachedAt: string;
  payload: SummarySnapshot;
};

export function severityClass(level: string | null | undefined): string {
  const normalized = (level ?? "").toLowerCase();
  if (normalized === "critical" || normalized === "high") return "severity-critical";
  if (normalized === "warn" || normalized === "warning" || normalized === "medium") {
    return "severity-warning";
  }
  return "severity-info";
}

function toInt(value: unknown): number | null {
  if (typeof value !== "number" || Number.isNaN(value)) return null;
  return Math.max(0, Math.min(999999, Math.round(value)));
}

function readCachedSummary(): CachedSummary | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(DASHBOARD_CACHE_KEY);
  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw) as CachedSummary;
    if (!parsed || typeof parsed !== "object") return null;
    if (typeof parsed.cachedAt !== "string") return null;
    if (!parsed.payload || typeof parsed.payload !== "object") return null;
    return parsed;
  } catch {
    return null;
  }
}

function writeCachedSummary(payload: SummarySnapshot): void {
  if (typeof window === "undefined") return;
  const record: CachedSummary = {
    cachedAt: new Date().toISOString(),
    payload,
  };
  window.localStorage.setItem(DASHBOARD_CACHE_KEY, JSON.stringify(record));
}

function parseIsoDate(value: string | null | undefined): Date | null {
  if (!value) return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function staleAgeMinutes(value: string | null | undefined): number | null {
  const parsed = parseIsoDate(value);
  if (!parsed) return null;
  return Math.max(0, Math.floor((Date.now() - parsed.getTime()) / 60000));
}

export function useDashboardSummary() {
  const summaryQuery = useQuery(DASHBOARD_SUMMARY, { pollInterval: 12000 });
  const healthQuery = useQuery(SYSTEM_HEALTH, { pollInterval: 15000 });
  const jobsQuery = useQuery(JOBS, { variables: { limit: 8 }, pollInterval: 10000 });
  const ragQuery = useQuery(RAG_STATUS, { pollInterval: 20000 });
  const alertsSub = useSubscription(SYSTEM_ALERTS);

  const [cached, setCached] = useState<CachedSummary | null>(null);

  useEffect(() => {
    setCached(readCachedSummary());
  }, []);

  const gatewayOffline = Boolean(
    summaryQuery.error || healthQuery.error || jobsQuery.error || ragQuery.error,
  );

  const liveSnapshot = useMemo<SummarySnapshot | null>(() => {
    const graph = summaryQuery.data?.dashboardSummary;
    const health = healthQuery.data?.systemHealth;
    const jobs = jobsQuery.data?.jobs ?? [];
    const rag = ragQuery.data?.ragStatus;

    const hasAnyLiveValue =
      Boolean(graph) ||
      Boolean(health) ||
      jobs.length > 0 ||
      Boolean(rag);

    if (!hasAnyLiveValue) return null;

    const jobsFromList = jobs.filter((job: { status?: string }) =>
      ["running", "queued", "pending"].includes(String(job.status ?? "").toLowerCase()),
    ).length;

    return {
      fraudAlerts: toInt(graph?.fraudAlerts),
      docsIndexed: toInt(graph?.docsIndexed ?? rag?.chunksCount),
      activeJobs: toInt(graph?.activeJobs ?? jobsFromList),
      riskScore: toInt(graph?.riskScore),
      healthStatus: health?.status ?? null,
      gatewayService: health?.service ?? null,
      uptimeSeconds:
        typeof health?.uptimeSeconds === "number" && !Number.isNaN(health.uptimeSeconds)
          ? health.uptimeSeconds
          : null,
      alertFeed: (graph?.alerts ?? []) as AlertRecord[],
    };
  }, [healthQuery.data, jobsQuery.data, ragQuery.data, summaryQuery.data]);

  const source: "live" | "cache" | "unavailable" =
    !gatewayOffline && liveSnapshot
      ? "live"
      : cached?.payload
        ? "cache"
        : "unavailable";

  useEffect(() => {
    if (source === "live" && liveSnapshot) {
      writeCachedSummary(liveSnapshot);
      setCached(readCachedSummary());
    }
  }, [liveSnapshot, source]);

  const snapshot = source === "live" ? liveSnapshot : cached?.payload ?? null;
  const streamAlert = alertsSub.data?.systemAlerts as AlertRecord | undefined;

  return {
    fraudAlerts: snapshot?.fraudAlerts ?? null,
    docsIndexed: snapshot?.docsIndexed ?? null,
    activeJobs: snapshot?.activeJobs ?? null,
    riskScore: snapshot?.riskScore ?? null,
    healthStatus: snapshot?.healthStatus ?? (source === "unavailable" ? "unavailable" : null),
    gatewayService: snapshot?.gatewayService ?? null,
    uptimeSeconds: snapshot?.uptimeSeconds ?? null,
    alertFeed: snapshot?.alertFeed ?? [],
    source,
    staleAgeMinutes: source === "cache" ? staleAgeMinutes(cached?.cachedAt) : null,
    gatewayOffline,
    streamAlert,
    refetch: () => Promise.all([summaryQuery.refetch(), healthQuery.refetch(), jobsQuery.refetch(), ragQuery.refetch()]),
  };
}
