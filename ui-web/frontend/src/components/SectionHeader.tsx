type Props = {
  eyebrow: string;
  title: string;
  description: string;
};

export default function SectionHeader({ eyebrow, title, description }: Props) {
  return (
    <div className="mb-8">
      <p className="tag text-moss">{eyebrow}</p>
      <h2 className="mt-4 text-3xl font-display font-semibold text-ink">{title}</h2>
      <p className="mt-3 max-w-2xl text-base text-fog">{description}</p>
    </div>
  );
}
