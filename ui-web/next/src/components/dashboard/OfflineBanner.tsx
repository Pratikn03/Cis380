export function OfflineBanner({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <section className="sf-warning-banner">
      <strong>{title}</strong>
      <span className="muted"> {subtitle}</span>
    </section>
  );
}
