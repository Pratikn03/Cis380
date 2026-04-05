type Props = {
  label: string;
  value: string;
};

export default function StatCard({ label, value }: Props) {
  return (
    <div className="card-panel px-5 py-6">
      <p className="text-xs uppercase tracking-[0.3em] text-moss">{label}</p>
      <p className="mt-3 text-2xl font-display font-semibold text-ink">{value}</p>
    </div>
  );
}
