import type { ReactNode } from "react";

type KpiCardProps = {
  label: string;
  value: ReactNode;
  subLabel: string;
  tone: "danger" | "teal" | "purple" | "amber";
};

export function KpiCard({ label, value, subLabel, tone }: KpiCardProps) {
  return (
    <article className={`dash-metric-card metric-${tone}`}>
      <div className="dash-metric-label">{label}</div>
      <div className="dash-metric-value">{value}</div>
      <div className="dash-metric-sub">{subLabel}</div>
    </article>
  );
}
