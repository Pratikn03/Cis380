"use client";

import { useMutation } from "@apollo/client";
import { useMemo, useState } from "react";
import { OfflineBanner } from "@/components/dashboard/OfflineBanner";
import { RUN_RISK, SCORE_BEHAVIOR, SCORE_CYBER, SCORE_FRAUD } from "@/lib/gateway-graphql";
import { domainPrimaryMetricPercent, useTrainingReadiness } from "@/lib/hooks/useTrainingReadiness";

function parseFeatures(raw: string): number[] {
  return raw
    .split(/[\s,]+/)
    .map((v) => v.trim())
    .filter(Boolean)
    .map(Number)
    .filter((n) => Number.isFinite(n));
}

function clampPercent(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(100, Math.round(value)));
}

function scoreToPercent(score: unknown, fallback: number | null = null): number | null {
  if (typeof score !== "number" || Number.isNaN(score)) return fallback;
  const normalized = score <= 1 ? score * 100 : score;
  return clampPercent(normalized);
}

function displayPercent(value: number | null): string {
  return value === null ? "--" : `${value}%`;
}

export default function RiskPage() {
  const [featureInput, setFeatureInput] = useState("0.42, -1.15, 2.04, 0.11, 0.87");
  const [riskOut, setRiskOut] = useState<Record<string, unknown> | null>(null);
  const [scoreOut, setScoreOut] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");

  const features = useMemo(() => parseFeatures(featureInput), [featureInput]);

  const [runRisk, { loading: loadingRisk }] = useMutation(RUN_RISK);
  const [scoreFraud, { loading: loadingFraud }] = useMutation(SCORE_FRAUD);
  const [scoreCyber, { loading: loadingCyber }] = useMutation(SCORE_CYBER);
  const [scoreBehavior, { loading: loadingBehavior }] = useMutation(SCORE_BEHAVIOR);
  const training = useTrainingReadiness();
  const { domainsByKey } = training;

  const runFusion = async () => {
    setError("");
    try {
      const out = await runRisk({
        variables: {
          input: {
            loginCountry: "US",
            deviceKnown: true,
            loginTime: 12,
            clicksPerMinute: 10,
            filesAccessed: 2,
            transactionAmount: Math.max(0, features[0] ?? 0),
          },
        },
      });
      setRiskOut(out.data?.runRisk ?? null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const runTabular = async () => {
    setError("");
    try {
      const [fraud, cyber, behavior] = await Promise.all([
        scoreFraud({ variables: { features } }),
        scoreCyber({ variables: { features } }),
        scoreBehavior({ variables: { features } }),
      ]);
      setScoreOut({
        fraud: fraud.data?.scoreFraud,
        cyber: cyber.data?.scoreCyber,
        behavior: behavior.data?.scoreBehavior,
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const fraudFallback = domainPrimaryMetricPercent(domainsByKey.fraud);
  const cyberFallback = domainPrimaryMetricPercent(domainsByKey.cyber);
  const behaviorFallback = domainPrimaryMetricPercent(domainsByKey.behavior);
  const visionFallback = domainPrimaryMetricPercent(domainsByKey.vision);

  const fraudPct = scoreToPercent(
    (scoreOut?.fraud as Record<string, unknown> | undefined)?.score,
    fraudFallback,
  );
  const cyberPct = scoreToPercent(
    (scoreOut?.cyber as Record<string, unknown> | undefined)?.score,
    cyberFallback,
  );
  const behaviorPct = scoreToPercent(
    (scoreOut?.behavior as Record<string, unknown> | undefined)?.score,
    behaviorFallback,
  );
  const videoPct = visionFallback;

  const fusionPct = scoreToPercent((riskOut as Record<string, unknown> | undefined)?.fusionRisk);
  const fusionRingPct = fusionPct ?? 0;
  const driftAuc = domainsByKey.vision?.metrics?.auc ?? domainsByKey.cyber?.metrics?.auc;
  const driftUpdated = domainsByKey.vision?.updatedAt ?? domainsByKey.cyber?.updatedAt;

  const summaryFeed = [
    {
      id: "AL-1120",
      severity: "High",
      text: (riskOut as Record<string, unknown> | undefined)?.reasonCode
        ? `Reason code: ${String((riskOut as Record<string, unknown>).reasonCode)}`
        : "Anomalous risk combination detected",
      progress: fusionPct ?? 0,
    },
    {
      id: "AL-1116",
      severity: "Medium",
      text: `Fraud=${displayPercent(fraudPct)} Cyber=${displayPercent(cyberPct)} Behavior=${displayPercent(behaviorPct)}`,
      progress: Math.round(
        (
          (fraudPct ?? 0) +
          (cyberPct ?? 0) +
          (behaviorPct ?? 0)
        ) / 3,
      ),
    },
  ];

  return (
    <div className="sf-page-stack">
      <section className="sf-page-head card">
        <div>
          <h1 className="sf-page-title">Risk Lab</h1>
          <p className="muted">Risk fusion + module scorers with anomaly tracking and action workflows.</p>
        </div>
        <div className="sf-tab-row">
          <button className="sf-tab sf-tab-active" type="button">Risk Fusion</button>
          <button className="sf-tab" type="button">Modules</button>
          <button className="sf-tab" type="button">Studies</button>
        </div>
      </section>

      {training.source === "cache" && (
        <OfflineBanner
          title="Training metrics cached:"
          subtitle={`showing last known values (${training.staleAgeMinutes ?? 0}m stale).`}
        />
      )}
      {training.source === "unavailable" && (
        <OfflineBanner
          title="Training metrics unavailable:"
          subtitle="run training/readiness once to populate live or cached risk metrics."
        />
      )}

      <section className="sf-two-col">
        <article className="card sf-stat-card">
          <div className="sf-panel-heading">Overall Risk Score</div>
          <div className="sf-risk-grid">
            <div
              className="sf-risk-ring"
              style={{
                background: `conic-gradient(var(--sf-gold) ${fusionRingPct}%, rgba(255,255,255,0.08) ${fusionRingPct}% 100%)`,
              }}
            >
              <div className="sf-risk-ring-inner">{displayPercent(fusionPct)}</div>
            </div>
            <div className="sf-risk-breakdown">
              <div><span>Fraud</span><strong>{displayPercent(fraudPct)}</strong></div>
              <div><span>Video</span><strong>{displayPercent(videoPct)}</strong></div>
              <div><span>Cyber</span><strong>{displayPercent(cyberPct)}</strong></div>
              <div><span>Behavior</span><strong>{displayPercent(behaviorPct)}</strong></div>
            </div>
          </div>
        </article>

        <article className="card sf-stat-card">
          <div className="sf-panel-heading">Training Drift</div>
          <p className="muted">Monitoring shift against previous baseline windows.</p>
          <svg viewBox="0 0 320 110" className="sf-drift-chart" role="img" aria-label="Training drift chart">
            <path d="M0 72 L48 74 L92 70 L136 58 L184 59 L228 42 L272 46 L320 22" />
            <circle cx="320" cy="22" r="4" />
          </svg>
          <div className="sf-mini-kpis">
            <div>
              <span>Last Audit</span>
              <strong>{driftUpdated ? new Date(driftUpdated).toLocaleDateString() : "n/a"}</strong>
            </div>
            <div>
              <span>Tracked AUC</span>
              <strong>{driftAuc == null ? "n/a" : `${Math.round(driftAuc * 100)}%`}</strong>
            </div>
          </div>
        </article>
      </section>

      <section className="card sf-feed-card">
        <div className="sf-panel-heading">Risk Summary Feed</div>
        <div className="sf-feed-list">
          {summaryFeed.map((item) => (
            <div key={item.id} className="sf-feed-row">
              <div className="sf-feed-id">ID: {item.id}</div>
              <div className="sf-feed-text">{item.text}</div>
              <div className="sf-feed-severity">{item.severity}</div>
              <div className="sf-feed-progress">
                <span style={{ width: `${item.progress}%` }} />
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="card panel-grid">
        <div className="sf-panel-heading">Feature Inputs</div>
        <textarea
          className="input"
          value={featureInput}
          onChange={(e) => setFeatureInput(e.target.value)}
          rows={3}
        />
        <div className="flex flex-wrap gap-3">
          <button className="pill-btn" onClick={runTabular}>
            {loadingFraud || loadingCyber || loadingBehavior ? "Scoring..." : "Run Module Scores"}
          </button>
          <button className="pill-btn" onClick={runFusion}>
            {loadingRisk ? "Analyzing..." : "Analyze Risk"}
          </button>
        </div>
      </section>

      {error && <div className="card">Error: {error}</div>}

      <section className="sf-action-strip">
        <button className="sf-strip-btn strip-purple" onClick={runFusion} type="button">Run Risk Fusion</button>
        <button className="sf-strip-btn strip-orange" onClick={runTabular} type="button">Run Module Scores</button>
        <button className="sf-strip-btn strip-blue" type="button">Export Investigation</button>
      </section>

      {(scoreOut || riskOut) && (
        <section className="sf-two-col">
          <article className="card">
            <div className="card-title">Score Output</div>
            <pre className="mt-3 whitespace-pre-wrap text-xs">{JSON.stringify(scoreOut, null, 2)}</pre>
          </article>
          <article className="card">
            <div className="card-title">Fusion Output</div>
            <pre className="mt-3 whitespace-pre-wrap text-xs">{JSON.stringify(riskOut, null, 2)}</pre>
          </article>
        </section>
      )}
    </div>
  );
}
