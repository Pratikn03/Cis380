import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { describe, expect, it } from "vitest";

describe("ModelsPage synthetic score guard", () => {
  it("does not contain metricFromName placeholder logic", () => {
    const thisFile = fileURLToPath(import.meta.url);
    const modelsFile = path.resolve(path.dirname(thisFile), "./models/page.tsx");
    const source = readFileSync(modelsFile, "utf-8");
    expect(source).not.toContain("metricFromName");
    expect(source).not.toContain("hash = Array.from");
  });
});

