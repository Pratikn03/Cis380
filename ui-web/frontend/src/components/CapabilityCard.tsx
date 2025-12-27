type Props = {
  title: string;
  description: string;
  tags: string[];
  metric: string;
};

export default function CapabilityCard({ title, description, tags, metric }: Props) {
  return (
    <div className="card-panel flex h-full flex-col gap-4 px-6 py-6">
      <div>
        <h3 className="text-xl font-display font-semibold text-ink">{title}</h3>
        <p className="mt-2 text-sm text-fog">{description}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        {tags.map((tag) => (
          <span key={tag} className="tag text-fog">
            {tag}
          </span>
        ))}
      </div>
      <p className="mt-auto text-sm font-semibold text-ember">{metric}</p>
    </div>
  );
}
