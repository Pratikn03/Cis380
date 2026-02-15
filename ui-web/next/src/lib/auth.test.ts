import { clearAuthToken, getAuthToken, hasAuthToken, setAuthToken } from "./auth";

describe("auth token helpers", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("stores and reads auth token", () => {
    setAuthToken("token-123");
    expect(getAuthToken()).toBe("token-123");
    expect(hasAuthToken()).toBe(true);
  });

  it("clears auth token", () => {
    setAuthToken("token-abc");
    clearAuthToken();
    expect(getAuthToken()).toBeNull();
    expect(hasAuthToken()).toBe(false);
  });

  it("dispatches auth-token-changed events", () => {
    const handler = vi.fn();
    window.addEventListener("auth-token-changed", handler);

    setAuthToken("token-a");
    clearAuthToken();

    expect(handler).toHaveBeenCalledTimes(2);
  });
});
