import { severityClass } from "@/lib/hooks/useDashboardSummary";

export type AlertItem = {
  level?: string | null;
  message?: string | null;
  timestamp?: string | null;
};

function formatTimestamp(value: string | null | undefined): string {
  if (!value) return "just now";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleTimeString();
}

export function AlertFeed({ items }: { items: AlertItem[] }) {
  return (
    <div className="dash-alert-list">
      {items.map((item, index) => (
        <div key={`${item.timestamp ?? "alert"}-${index}`} className="dash-alert-item">
          <span className={`severity-pill ${severityClass(item.level)}`}>{item.level ?? "info"}</span>
          <span className="dash-alert-message">{item.message ?? "No message"}</span>
          <span className="dash-alert-time">{formatTimestamp(item.timestamp)}</span>
        </div>
      ))}
    </div>
  );
}
