import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

function read(relativePath: string): string {
  const here = fileURLToPath(import.meta.url);
  return readFileSync(path.resolve(path.dirname(here), relativePath), "utf-8");
}

describe("dashboard/training source-state contracts", () => {
  it("dashboard hook stores last-known real snapshot and has no synthetic constants", () => {
    const source = read("./useDashboardSummary.ts");

    expect(source).toContain("sf:last_dashboard_summary");
    expect(source).toContain("\"live\" | \"cache\" | \"unavailable\"");
    expect(source).not.toContain("scoreToInt(graph?.fraudAlerts, 12)");
    expect(source).not.toContain("scoreToInt(graph?.docsIndexed ?? rag?.chunksCount, gatewayOffline ? 238 : 0)");
    expect(source).not.toContain("scoreToInt(graph?.riskScore, 58)");
  });

  it("training hook stores last-known overview and exposes freshness semantics", () => {
    const source = read("./useTrainingReadiness.ts");

    expect(source).toContain("sf:last_training_overview");
    expect(source).toContain("\"live\" | \"cache\" | \"unavailable\"");
    expect(source).toContain("staleAgeMinutes");
    expect(source).toContain("hasBlockers");
  });
});
