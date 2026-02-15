export function SignalChart({ kind }: { kind: "line" | "bars" }) {
  if (kind === "bars") {
    return (
      <div className="dash-bars">
        {[22, 38, 26, 47, 31, 42].map((value, index) => (
          <span key={index} style={{ height: `${value}px` }} />
        ))}
      </div>
    );
  }

  return (
    <svg viewBox="0 0 240 64" className="dash-line-chart" role="img" aria-label="Signal trend">
      <path d="M0 54 L35 46 L60 34 L88 38 L118 25 L148 29 L180 18 L212 22 L240 10" />
    </svg>
  );
}
