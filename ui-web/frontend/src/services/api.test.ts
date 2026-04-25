import { api, authStorage, clearAuthTokens, fetchAgentStream, setAuthTokens } from "./api";

describe("compatibility axios client", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("injects Authorization header when auth token exists", async () => {
    localStorage.setItem(authStorage.access, "token-xyz");
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

  it("sets and clears local auth tokens", () => {
    setAuthTokens("access-1", "refresh-1");
    expect(localStorage.getItem(authStorage.access)).toBe("access-1");
    expect(localStorage.getItem(authStorage.refresh)).toBe("refresh-1");

    clearAuthTokens();
    expect(localStorage.getItem(authStorage.access)).toBeNull();
    expect(localStorage.getItem(authStorage.refresh)).toBeNull();
  });

  it("parses agent SSE stream events", async () => {
    setAuthTokens("stream-token");
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(
          new TextEncoder().encode(
            [
              'event: step\ndata: {"tool":"vision","status":"running"}',
              'event: token\ndata: {"text":"hello"}',
              'event: citation\ndata: {"title":"policy","url":"https://example.test"}',
              'event: final\ndata: {"confidence":0.91}',
              "",
            ].join("\n\n"),
          ),
        );
        controller.close();
      },
    });
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      body: stream,
    } as Response);
    const events: unknown[] = [];

    await fetchAgentStream(new FormData(), (event) => events.push(event));

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining("/api/agent/stream"),
      expect.objectContaining({
        method: "POST",
        headers: { Authorization: "Bearer stream-token" },
      }),
    );
    expect(events).toEqual([
      { type: "step", data: { tool: "vision", status: "running" } },
      { type: "token", data: { text: "hello" } },
      { type: "citation", data: { title: "policy", url: "https://example.test" } },
      { type: "final", data: { confidence: 0.91 } },
    ]);
  });

  it("raises a clear error when agent stream cannot start", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 503,
      body: null,
    } as Response);

    await expect(fetchAgentStream(new FormData(), vi.fn())).rejects.toThrow(
      "Agent stream failed (503)",
    );
  });
});
