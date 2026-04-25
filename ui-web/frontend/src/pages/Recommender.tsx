import { useMemo, useState } from "react";
import { ErrorState, JsonBlock, PageShell, Panel, PrimaryButton, TextInput } from "../components/DashboardPrimitives";
import { api } from "../services/api";

export default function Recommender() {
  const [userId, setUserId] = useState("web_user");
  const [result, setResult] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const items = useMemo(() => result?.items || [], [result]);
  const diversity = useMemo(() => {
    const tags = new Set<string>();
    items.forEach((item: any) => String(item.tags || item.category || "").split(/[,\s]+/).forEach((tag) => tag && tags.add(tag)));
    return items.length ? Number((tags.size / items.length).toFixed(2)) : 0;
  }, [items]);

  const run = async () => {
    setError(null);
    try {
      const { data } = await api.post("/api/recommend", { user_id: userId, top_k: 8 });
      setResult(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  return (
    <PageShell title="Recommender" eyebrow="Per-user Recommendations">
      <div className="grid gap-4 lg:grid-cols-[22rem_1fr]">
        <Panel title="User">
          <TextInput value={userId} onChange={(event) => setUserId(event.target.value)} />
          <PrimaryButton onClick={run} className="mt-3">
            Load Recommendations
          </PrimaryButton>
          <ErrorState message={error} />
          <p className="mt-4 text-sm text-fog">Diversity metric: <strong>{diversity}</strong></p>
        </Panel>
        <Panel title="Recommendations">
          <div className="grid gap-3 md:grid-cols-2">
            {items.map((item: any) => (
              <article key={item.item_id || item.title} className="rounded-md border border-line bg-white p-3">
                <h3 className="font-semibold">{item.title || item.item_id}</h3>
                <p className="text-sm text-fog">Score {Number(item.score || 0).toFixed(3)}</p>
                <p className="text-xs text-fog">{item.tags || item.source || item.category}</p>
              </article>
            ))}
          </div>
          {items.length === 0 && <JsonBlock value={result || { items: [] }} />}
        </Panel>
      </div>
    </PageShell>
  );
}
