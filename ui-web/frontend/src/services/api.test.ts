import { api } from "./api";

describe("legacy axios client", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("injects Authorization header when auth token exists", async () => {
    localStorage.setItem("AUTH_TOKEN", "token-xyz");
    const fulfilled = api.interceptors.request.handlers[0]?.fulfilled;
    expect(fulfilled).toBeDefined();

    const config = await fulfilled?.({ headers: {} });
    expect(config?.headers?.Authorization).toBe("Bearer token-xyz");
  });

  it("does not inject Authorization header when auth token is absent", async () => {
    const fulfilled = api.interceptors.request.handlers[0]?.fulfilled;
    expect(fulfilled).toBeDefined();

    const config = await fulfilled?.({ headers: {} });
    expect(config?.headers?.Authorization).toBeUndefined();
  });
});
