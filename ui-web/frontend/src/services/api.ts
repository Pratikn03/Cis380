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

export type AgentStreamEvent =
  | { type: "step"; data: Record<string, unknown> }
  | { type: "token"; data: { text?: string } }
  | { type: "citation"; data: Record<string, unknown> }
  | { type: "final"; data: Record<string, unknown> }
  | { type: "error"; data: Record<string, unknown> };

export async function fetchAgentStream(
  payload: FormData,
  onEvent: (event: AgentStreamEvent) => void,
) {
  const base = api.defaults.baseURL || resolveApiBase();
  const url = `${String(base).replace(/\/$/, "")}/api/agent/stream`;
  const token = localStorage.getItem(authStorage.access);
  const response = await fetch(url, {
    method: "POST",
    body: payload,
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
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
      const data = JSON.parse(dataLine.replace("data:", "").trim());
      onEvent({ type, data } as AgentStreamEvent);
    }
  }
}
