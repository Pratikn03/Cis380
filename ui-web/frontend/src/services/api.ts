import axios from "axios";

export const resolveApiBase = () => {
  const envBase = import.meta.env.VITE_API_BASE;
  if (envBase && envBase.trim().length > 0) {
    return envBase;
  }
  if (import.meta.env.MODE === "development") {
    return "http://localhost:8000";
  }
  if (typeof window !== "undefined") {
    return window.location.origin;
  }
  return "http://localhost:8000";
};

export const api = axios.create({
  baseURL: resolveApiBase(),
  timeout: 120000,
});

export const authStorage = {
  access: "AUTH_TOKEN",
  refresh: "REFRESH_TOKEN",
};

export const setAuthTokens = (accessToken: string, refreshToken?: string) => {
  localStorage.setItem(authStorage.access, accessToken);
  if (refreshToken) {
    localStorage.setItem(authStorage.refresh, refreshToken);
  }
};

export const clearAuthTokens = () => {
  localStorage.removeItem(authStorage.access);
  localStorage.removeItem(authStorage.refresh);
};

// Request interceptor to inject the JWT token if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(authStorage.access);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const refreshToken = localStorage.getItem(authStorage.refresh);
    if (error.response?.status === 401 && refreshToken && !original?._retry) {
      original._retry = true;
      const { data } = await api.post("/api/v1/auth/refresh", {
        refresh_token: refreshToken,
      });
      if (data?.access_token) {
        setAuthTokens(data.access_token, data.refresh_token);
        original.headers = original.headers || {};
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      }
    }
    return Promise.reject(error);
  },
);

/**
 * SSE event names produced by /api/v1/agent/run.
 *
 * Legacy aliases (`step`, `token`, `citation`, `final`) are kept so the old
 * /api/agent/stream consumer keeps compiling; new code should consume the
 * v1 names directly.
 */
export type AgentStreamEvent =
  | { type: "trace_start"; data: Record<string, unknown> }
  | { type: "triage"; data: Record<string, unknown> }
  | { type: "thinking_delta"; data: { text?: string } }
  | { type: "tool_call"; data: Record<string, unknown> }
  | { type: "tool_result"; data: Record<string, unknown> }
  | { type: "tool_error"; data: Record<string, unknown> }
  | { type: "safety_blocked"; data: Record<string, unknown> }
  | { type: "final_message"; data: Record<string, unknown> }
  | { type: "usage"; data: Record<string, unknown> }
  | { type: "final_envelope"; data: { envelope?: Record<string, unknown> } }
  | { type: "trace_end"; data: Record<string, unknown> }
  // legacy /api/agent/stream aliases:
  | { type: "step"; data: Record<string, unknown> }
  | { type: "token"; data: { text?: string } }
  | { type: "citation"; data: Record<string, unknown> }
  | { type: "final"; data: Record<string, unknown> }
  | { type: "error"; data: Record<string, unknown> };

export interface AgentStreamOptions {
  /** Override the endpoint. Defaults to /api/v1/agent/run. */
  url?: string;
  /** AbortSignal to stop the stream early. */
  signal?: AbortSignal;
}

export async function fetchAgentStream(
  payload: FormData,
  onEvent: (event: AgentStreamEvent) => void,
  options: AgentStreamOptions = {},
) {
  const base = api.defaults.baseURL || resolveApiBase();
  const url =
    options.url ||
    `${String(base).replace(/\/$/, "")}/api/v1/agent/run`;
  const token = localStorage.getItem(authStorage.access);
  const response = await fetch(url, {
    method: "POST",
    body: payload,
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    signal: options.signal,
  });
  if (!response.ok || !response.body) {
    throw new Error(`Agent stream failed (${response.status})`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() || "";
    for (const frame of frames) {
      const eventLine = frame.split("\n").find((line) => line.startsWith("event:"));
      const dataLine = frame.split("\n").find((line) => line.startsWith("data:"));
      if (!eventLine || !dataLine) continue;
      const type = eventLine.replace("event:", "").trim() as AgentStreamEvent["type"];
      let data: Record<string, unknown>;
      try {
        data = JSON.parse(dataLine.replace("data:", "").trim());
      } catch {
        continue;
      }
      onEvent({ type, data } as AgentStreamEvent);
    }
  }
}
