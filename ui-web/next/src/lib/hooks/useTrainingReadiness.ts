"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@apollo/client";
import { TRAINING_OVERVIEW } from "@/lib/gateway-graphql";

const TRAINING_CACHE_KEY = "sf:last_training_overview";

export type TrainingMetrics = {
  accuracy?: number | null;
  f1?: number | null;
  auc?: number | null;
  precision?: number | null;
  recall?: number | null;
};

export type TrainingDomain = {
  domain: string;
  status: string;
  datasetReady: boolean;
  modelReady: boolean;
  metrics?: TrainingMetrics | null;
  sourcePath: string;
  updatedAt?: string | null;
  blockers: string[];
  qualityStatus: string;
  thresholds?: unknown;
  metricFailures: string[];
  artifactSha256?: string | null;
};

type TrainingOverview = {
  generatedAt?: string | null;
  readyCount?: number | null;
  totalCount?: number | null;
  domains?: TrainingDomain[];
};

type TrainingOverviewData = {
  trainingOverview: TrainingOverview;
};

type CachedTrainingOverview = {
  cachedAt: string;
  payload: TrainingOverview;
};

const READY_ALIASES = new Set(["ok", "ready", "green", "pass", "passed", "fresh"]);
const DEGRADED_ALIASES = new Set([
  "warn",
  "warning",
  "yellow",
  "degraded",
  "needs_preprocess",
  "stale",
  "soft",
  "soft_gate",
]);
const BLOCKED_ALIASES = new Set([
  "missing",
  "error",
  "critical",
  "red",
  "fail",
  "failed",
  "mismatch",
  "blocked",
]);
const ADVISORY_ALIASES = new Set(["advisory", "historical", "manual"]);

function parseIsoDate(value: string | null | undefined): Date | null {
  if (!value) return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function getStaleAgeMinutes(value: string | null | undefined): number | null {
  const parsed = parseIsoDate(value);
  if (!parsed) return null;
  return Math.max(0, Math.floor((Date.now() - parsed.getTime()) / 60000));
}

function readCachedOverview(): CachedTrainingOverview | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(TRAINING_CACHE_KEY);
  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw) as CachedTrainingOverview;
    if (!parsed || typeof parsed !== "object") return null;
    if (typeof parsed.cachedAt !== "string") return null;
    if (!parsed.payload || typeof parsed.payload !== "object") return null;
    return parsed;
  } catch {
    return null;
  }
}

function writeCachedOverview(payload: TrainingOverview): void {
  if (typeof window === "undefined") return;
  const record: CachedTrainingOverview = {
    cachedAt: new Date().toISOString(),
    payload,
  };
  window.localStorage.setItem(TRAINING_CACHE_KEY, JSON.stringify(record));
}

function countReady(domains: TrainingDomain[]): number {
  return domains.filter((domain) => isTrainingReadyStatus(domain.status)).length;
}

export function normalizeTrainingStatus(status: string | null | undefined): string {
  const normalized = (status ?? "").trim().toLowerCase().replace(/-/g, "_");
  if (!normalized) return "blocked";
  if (READY_ALIASES.has(normalized)) return "ready";
  if (DEGRADED_ALIASES.has(normalized)) return "degraded";
  if (BLOCKED_ALIASES.has(normalized)) return "blocked";
  if (ADVISORY_ALIASES.has(normalized)) return "advisory";
  return normalized;
}

export function isTrainingReadyStatus(status: string | null | undefined): boolean {
  return normalizeTrainingStatus(status) === "ready";
}

export function isTrainingBlockingStatus(status: string | null | undefined): boolean {
  return normalizeTrainingStatus(status) === "blocked";
}

export function metricToPercent(value: number | null | undefined): number | null {
  if (typeof value !== "number" || Number.isNaN(value)) return null;
  const normalized = value <= 1 ? value * 100 : value;
  return Math.max(0, Math.min(100, Math.round(normalized)));
}

export function domainPrimaryMetricPercent(domain: TrainingDomain | undefined): number | null {
  if (!domain?.metrics) return null;
  const preferred = [
    domain.metrics.auc,
    domain.metrics.f1,
    domain.metrics.accuracy,
    domain.metrics.precision,
    domain.metrics.recall,
  ];
  for (const value of preferred) {
    const pct = metricToPercent(value);
    if (pct !== null) return pct;
  }
  return null;
}

export function useTrainingReadiness() {
  const query = useQuery<TrainingOverviewData>(TRAINING_OVERVIEW, {
    pollInterval: 30000,
  });

  const [cached, setCached] = useState<CachedTrainingOverview | null>(null);

  useEffect(() => {
    setCached(readCachedOverview());
  }, []);

  const liveOverview = query.data?.trainingOverview;
  const liveDomains = liveOverview?.domains ?? [];
  const hasLiveDomains = liveDomains.length > 0;

  useEffect(() => {
    if (!query.error && hasLiveDomains && liveOverview) {
      writeCachedOverview(liveOverview);
      setCached(readCachedOverview());
    }
  }, [hasLiveDomains, liveOverview, query.error]);

  const source: "live" | "cache" | "unavailable" = hasLiveDomains
    ? "live"
    : cached?.payload?.domains?.length
      ? "cache"
      : "unavailable";

  const effectiveOverview = source === "live" ? liveOverview : cached?.payload;
  const domains = useMemo(
    () =>
      (effectiveOverview?.domains ?? []).map((domain) => ({
        ...domain,
        status: normalizeTrainingStatus(domain.status),
        blockers: Array.isArray(domain.blockers) ? domain.blockers : [],
        metricFailures: Array.isArray(domain.metricFailures) ? domain.metricFailures : [],
      })),
    [effectiveOverview?.domains],
  );

  const domainsByKey = useMemo(() => {
    const map: Record<string, TrainingDomain> = {};
    for (const domain of domains) {
      map[domain.domain.toLowerCase()] = domain;
    }
    return map;
  }, [domains]);

  const readyCount =
    effectiveOverview?.readyCount ?? countReady(domains);
  const totalCount =
    effectiveOverview?.totalCount ?? domains.length;

  const hasBlockers = domains.some(
    (domain) => domain.blockers.length > 0 || isTrainingBlockingStatus(domain.status),
  );
  const staleAgeMinutes =
    source === "live"
      ? getStaleAgeMinutes(effectiveOverview?.generatedAt)
      : getStaleAgeMinutes(cached?.cachedAt ?? null);

  const state: "loading" | "ready" | "empty" | "offline" | "error" = (() => {
    if (source === "unavailable" && query.loading) return "loading";
    if (source === "unavailable" && query.error) return "offline";
    if (!domains.length) return "empty";
    if (domains.every((domain) => isTrainingReadyStatus(domain.status))) return "ready";
    return "error";
  })();

  return {
    state,
    source,
    staleAgeMinutes,
    hasBlockers,
    domains,
    domainsByKey,
    generatedAt: effectiveOverview?.generatedAt ?? null,
    readyCount,
    totalCount,
    error: query.error?.message ?? null,
    refetch: query.refetch,
  };
}
