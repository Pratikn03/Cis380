import { TrainingDomainCard } from "@/components/dashboard/TrainingDomainCard";
import type { TrainingDomain } from "@/lib/hooks/useTrainingReadiness";

type Props = {
  domains: TrainingDomain[];
  readyCount: number;
  totalCount: number;
  generatedAt: string | null;
  source: "live" | "cache" | "unavailable";
  staleAgeMinutes: number | null;
  hasBlockers: boolean;
  onRefresh?: () => Promise<unknown> | void;
  refreshing?: boolean;
};

export function TrainingReadinessStrip({
  domains,
  readyCount,
  totalCount,
  generatedAt,
  source,
  staleAgeMinutes,
  hasBlockers,
  onRefresh,
  refreshing = false,
}: Props) {
  return (
    <section className="sf-training-strip">
      <header className="card sf-training-header">
        <div>
          <div className="card-title">Training Readiness</div>
          <h3 className="sf-training-title">
            {readyCount}/{totalCount} domains ready
          </h3>
        </div>
        <div className="sf-training-head-meta">
          <span className={`sf-source-chip sf-source-${source}`}>source: {source}</span>
          <span className="sf-training-generated">
            Last audit: {generatedAt ? generatedAt : "not available"}
          </span>
          {source === "cache" && (
            <span className="sf-training-generated">stale: {staleAgeMinutes ?? 0}m</span>
          )}
          {hasBlockers && <span className="sf-blocker-pill">blockers present</span>}
          {onRefresh && (
            <button className="pill-btn" type="button" onClick={() => void onRefresh()} disabled={refreshing}>
              {refreshing ? "Refreshing readiness..." : "Refresh Training Readiness"}
            </button>
          )}
        </div>
      </header>

      {domains.length > 0 ? (
        <div className="sf-training-grid">
          {domains.map((domain) => (
            <TrainingDomainCard key={domain.domain} domain={domain} />
          ))}
        </div>
      ) : (
        <article className="card sf-training-empty">Training readiness data unavailable.</article>
      )}
    </section>
  );
}
