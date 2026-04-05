import { describe, expect, it } from "vitest";
import {
  isTrainingBlockingStatus,
  isTrainingReadyStatus,
  normalizeTrainingStatus,
} from "./useTrainingReadiness";

describe("training readiness status helpers", () => {
  it("normalizes degraded aliases into the canonical degraded state", () => {
    expect(normalizeTrainingStatus("DEGRADED")).toBe("degraded");
    expect(normalizeTrainingStatus("warning")).toBe("degraded");
    expect(normalizeTrainingStatus("soft-gate")).toBe("degraded");
  });

  it("normalizes blocking aliases into the canonical blocked state", () => {
    expect(normalizeTrainingStatus("missing")).toBe("blocked");
    expect(normalizeTrainingStatus("FAILED")).toBe("blocked");
    expect(isTrainingBlockingStatus("critical")).toBe(true);
  });

  it("preserves ready aliases for readiness counts", () => {
    expect(normalizeTrainingStatus("fresh")).toBe("ready");
    expect(isTrainingReadyStatus("ready")).toBe(true);
    expect(isTrainingReadyStatus("green")).toBe(true);
    expect(isTrainingReadyStatus("degraded")).toBe(false);
  });
});
