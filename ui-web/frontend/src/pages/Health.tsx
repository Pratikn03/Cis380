import { useEffect, useState } from "react";
import { ErrorState, JsonBlock, PageShell, Panel, StatusPill } from "../components/DashboardPrimitives";
import { healthDetailed } from "../services/endpoints";

export default function Health() {
  const [health, setHealth] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    healthDetailed()
      .then((response) => setHealth(response.data))
      .catch((err) => setError(err.response?.data?.detail || err.message));
  }, []);

  const components = health?.components || [];

  return (
    <PageShell title="Health" eyebrow="Protected Diagnostics">
      <ErrorState message={error} />
      <div className="grid gap-4 md:grid-cols-3">
        {components.map((component: any) => (
          <Panel key={component.name} title={component.name}>
            <StatusPill status={component.status} />
            <p className="mt-2 text-sm text-fog">{component.message}</p>
            {component.details && <JsonBlock value={component.details} />}
          </Panel>
        ))}
      </div>
      <Panel title="Detailed Payload" className="mt-4">
        <JsonBlock value={health || {}} />
      </Panel>
    </PageShell>
  );
}
