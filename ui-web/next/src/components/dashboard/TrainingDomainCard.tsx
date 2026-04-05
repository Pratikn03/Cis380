import { domainPrimaryMetricPercent, type TrainingDomain } from "@/lib/hooks/useTrainingReadiness";

function statusClass(status: string): string {
  const low = status.toLowerCase();
  if (low === "ready") return "severity-info";
  if (low === "warning") return "severity-warning";
  return "severity-critical";
}

type Props = {
  domain: TrainingDomain;
};

export function TrainingDomainCard({ domain }: Props) {
  const score = domainPrimaryMetricPercent(domain);
  const blockerCount = domain.blockers.length;

  return (
    <article className="card sf-training-card">
      <div className="sf-training-headline">
        <strong>{domain.domain.toUpperCase()}</strong>
        <span className={`severity-pill ${statusClass(domain.status)}`}>{domain.status}</span>
      </div>
      <div className="sf-training-flags">
        <span>Dataset: {domain.datasetReady ? "ready" : "missing"}</span>
        <span>Model: {domain.modelReady ? "ready" : "missing"}</span>
      </div>
      <div className="sf-training-score">{score === null ? "n/a" : `${score}%`}</div>
      <div className="sf-training-meta">
        <span>{domain.updatedAt ? new Date(domain.updatedAt).toLocaleString() : "no timestamp"}</span>
        <span>{domain.sourcePath ? "metrics linked" : "metrics missing"}</span>
        <span>{blockerCount > 0 ? `${blockerCount} blocker(s)` : "no blockers"}</span>
      </div>
      {domain.blockers.length > 0 && (
        <div className="sf-training-blockers">{domain.blockers.join(", ")}</div>
      )}
    </article>
  );
}
