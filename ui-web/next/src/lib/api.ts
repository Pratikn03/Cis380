export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const base = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
  const token = typeof window !== "undefined" ? localStorage.getItem("AUTH_TOKEN") : null;

  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  headers.set("x-request-id", crypto.randomUUID());
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${base}${path}`, {
    ...init,
    headers,
  });
  const text = await res.text();
  if (!res.ok) {
    throw new Error(text || `HTTP ${res.status}`);
  }
  return text ? (JSON.parse(text) as T) : ({} as T);
}
