import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { describe, expect, it } from "vitest";

function file(relativePath: string): string {
  const here = fileURLToPath(import.meta.url);
  return readFileSync(path.resolve(path.dirname(here), relativePath), "utf-8");
}

describe("training visibility smoke", () => {
  it("home and models pages are wired to training visibility surfaces", () => {
    const home = file("./page.tsx");
    const models = file("./models/page.tsx");

    expect(home).toContain("TrainingReadinessStrip");
    expect(home).toContain("useTrainingReadiness");

    expect(models).toContain("useTrainingReadiness");
    expect(models).toContain("domainPrimaryMetricPercent");
  });
});

