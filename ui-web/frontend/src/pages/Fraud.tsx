import { useMemo, useState } from "react";
import {
  ErrorState,
  JsonBlock,
  MiniBarChart,
  PageShell,
  Panel,
  PrimaryButton,
  TextArea,
} from "../components/DashboardPrimitives";
import { fraudExplain, fraudScore } from "../services/endpoints";

const parseFeatures = (raw: string) =>
  raw
    .split(/[\s,]+/)
    .map((item) => Number(item.trim()))
    .filter((item) => Number.isFinite(item));

export default function Fraud() {
  const [features, setFeatures] = useState("120.5, 0.2, 3, 0.7, 1.4, 0.1");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [explain, setExplain] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const chart = useMemo(() => {
    const explanation = explain?.explanation as Record<string, unknown> | undefined;
    const contributions = explanation?.feature_contributions as Record<string, number> | undefined;
    return Object.entries(contributions || {})
      .slice(0, 8)
      .map(([label, value]) => ({ label, value: Math.abs(Number(value)) }));
  }, [explain]);

  // The model expects a fixed feature shape; when the user submits fewer
  // values the API silently zero-pads, which masks the score. We warn here
  // so the operator knows the score reflects "supplied + zeros", not
  // their full row.
  const featureWarning = useMemo(() => {
    if (!result) return null;
    const expected = Number((result as any).expected_features || 0);
    const supplied = Number((result as any).input_features || 0);
    if (expected && supplied && supplied !== expected) {
      return `You supplied ${supplied} features; the model expects ${expected}. Missing slots were zero-padded — the score may be unreliable.`;
    }
    return null;
  }, [result]);

  const run = async () => {
    setError(null);
    const values = parseFeatures(features);
    try {
      const [scoreResponse, explainResponse] = await Promise.all([
        fraudScore({ features: values }),
        fraudExplain({ features: values }),
      ]);
      setResult(scoreResponse.data);
      setExplain(explainResponse.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Fraud request failed");
    }
  };

  return (
    <PageShell title="Fraud" eyebrow="Feature Heatmap + SHAP">
      <div className="grid gap-4 lg:grid-cols-[24rem_1fr]">
        <Panel title="Transaction Features">
          <TextArea rows={8} value={features} onChange={(event) => setFeatures(event.target.value)} />
          <PrimaryButton onClick={run} className="mt-3">
            Score + Explain
          </PrimaryButton>
          <ErrorState message={error} />
        </Panel>
        <div className="space-y-4">
          <Panel title="Decision">
            {featureWarning && (
              <div className="mb-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                {featureWarning}
              </div>
            )}
            {result ? <JsonBlock value={result} /> : <p className="text-sm text-fog">Run a transaction score.</p>}
          </Panel>
          <Panel title="Decision Boundary Explainer">
            {chart.length > 0 ? <MiniBarChart data={chart} /> : <p className="text-sm text-fog">SHAP output appears after scoring.</p>}
            {Boolean(explain?.degraded) && (
              <p className="mt-3 text-sm text-amber-700">Explanation is degraded; SHAP backend returned fallback feature contributions.</p>
            )}
          </Panel>
        </div>
      </div>
    </PageShell>
  );
}
