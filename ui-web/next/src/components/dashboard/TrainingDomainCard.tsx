import {
  domainPrimaryMetricPercent,
  normalizeTrainingStatus,
  type TrainingDomain,
} from "@/lib/hooks/useTrainingReadiness";

function statusClass(status: string): string {
  const normalized = normalizeTrainingStatus(status);
  if (normalized === "ready" || normalized === "advisory") return "severity-info";
  if (normalized === "degraded") return "severity-warning";
  return "severity-critical";
}

type Props = {
  domain: TrainingDomain;
};

export function TrainingDomainCard({ domain }: Props) {
  const score = domainPrimaryMetricPercent(domain);
  const blockerCount = domain.blockers.length;
  const normalizedStatus = normalizeTrainingStatus(domain.status);

  return (
    <article className="card sf-training-card">
      <div className="sf-training-headline">
        <strong>{domain.domain.toUpperCase()}</strong>
        <span className={`severity-pill ${statusClass(normalizedStatus)}`}>{normalizedStatus}</span>
      </div>
      <div className="sf-training-flags">
        <span>Dataset: {domain.datasetReady ? "ready" : "missing"}</span>
        <span>Model: {domain.modelReady ? "ready" : "missing"}</span>
      </div>
      <div className="sf-training-score">{score === null ? "n/a" : `${score}%`}</div>
      <div className="sf-training-meta">
        <span>{domain.updatedAt ? new Date(domain.updatedAt).toLocaleString() : "no timestamp"}</span>
        <span>{domain.metrics ? "metrics linked" : "metrics missing"}</span>
        <span>{blockerCount > 0 ? `${blockerCount} blocker(s)` : "no blockers"}</span>
      </div>
      {domain.blockers.length > 0 && (
        <div className="sf-training-blockers">{domain.blockers.join(", ")}</div>
      )}
    </article>
  );
}
