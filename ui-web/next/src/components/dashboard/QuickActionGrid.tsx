import Link from "next/link";

type QuickAction = {
  href: string;
  label: string;
  tone: "amber" | "cyan" | "pink" | "blue";
};

export function QuickActionGrid({ actions }: { actions: QuickAction[] }) {
  return (
    <div className="dash-actions-list">
      {actions.map((action) => (
        <Link key={`${action.href}-${action.label}`} href={action.href} className={`dash-action-btn action-${action.tone}`}>
          {action.label}
        </Link>
      ))}
    </div>
  );
}
