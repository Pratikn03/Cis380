import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { describe, expect, it } from "vitest";

function read(relativePath: string): string {
  const here = fileURLToPath(import.meta.url);
  return readFileSync(path.resolve(path.dirname(here), relativePath), "utf-8");
}

describe("route state contracts", () => {
  it("home route keeps resilient training and gateway banners", () => {
    const source = read("./page.tsx");
    expect(source).toContain("useTrainingReadiness");
    expect(source).toContain("OfflineBanner");
    expect(source).toContain("training.source === \"cache\"");
    expect(source).toContain("training.source === \"unavailable\"");
    expect(source).toContain("TrainingReadinessStrip");
    expect(source).toContain("onRefresh={() => runRefresh(\"training\")}");
    expect(source).toContain("Refresh Dashboard");
    expect(source).toContain("Inspect Active Jobs");
    expect(source).toContain("Open Model Registry");
    expect(source).toContain("formatMetric");
  });

  it("risk route derives fallback metrics from training readiness", () => {
    const source = read("./risk/page.tsx");
    expect(source).toContain("useTrainingReadiness");
    expect(source).toContain("domainPrimaryMetricPercent");
    expect(source).toContain("const driftAuc");
    expect(source).toContain("Tracked AUC");
    expect(source).not.toContain("?? 30");
    expect(source).not.toContain("?? 32");
    expect(source).not.toContain("?? 57");
    expect(source).not.toContain("?? 27");
    expect(source).not.toContain("fusionRisk, 58");
  });

  it("models route reads score from training metrics and avoids synthetic hash scoring", () => {
    const source = read("./models/page.tsx");
    expect(source).toContain("useTrainingReadiness");
    expect(source).toContain("domainPrimaryMetricPercent");
    expect(source).not.toContain("metricFromName");
    expect(source).not.toContain("Array.from(name).reduce");
  });

  it("datasets route shows training readiness and blockers", () => {
    const source = read("./datasets/page.tsx");
    expect(source).toContain("useTrainingReadiness");
    expect(source).toContain("Training Data Readiness");
    expect(source).toContain("domain.blockers");
    expect(source).toContain("training.source === \"cache\"");
    expect(source).toContain("training.source === \"unavailable\"");
  });
});
