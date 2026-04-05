import { afterEach, describe, expect, it, vi } from "vitest";

async function loadRuntime() {
  vi.resetModules();
  return import("./runtime");
}

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

describe("runtime auth mode", () => {
  it("defaults to jwt in production", async () => {
    vi.stubEnv("NODE_ENV", "production");

    const { authModeLabel, getAuthMode } = await loadRuntime();

    expect(getAuthMode()).toBe("jwt");
    expect(authModeLabel("jwt")).toBe("JWT");
  });

  it("clamps disabled to jwt in production", async () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("NEXT_PUBLIC_AUTH_MODE", "disabled");

    const { getAuthMode } = await loadRuntime();

    expect(getAuthMode()).toBe("jwt");
  });

  it("allows disabled only outside production", async () => {
    vi.stubEnv("NODE_ENV", "development");

    const { getAuthMode } = await loadRuntime();

    expect(getAuthMode()).toBe("disabled");
  });

  it("honors explicit jwt outside production", async () => {
    vi.stubEnv("NODE_ENV", "development");
    vi.stubEnv("NEXT_PUBLIC_AUTH_MODE", "jwt");

    const { getAuthMode } = await loadRuntime();

    expect(getAuthMode()).toBe("jwt");
  });
});
