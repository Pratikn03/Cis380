const AUTH_TOKEN_KEY = "AUTH_TOKEN";

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setAuthToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(AUTH_TOKEN_KEY, token);
  window.dispatchEvent(new Event("auth-token-changed"));
}

export function clearAuthToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(AUTH_TOKEN_KEY);
  window.dispatchEvent(new Event("auth-token-changed"));
}

export function clearAuthSession(): void {
  clearAuthToken();
}

export function hasAuthToken(): boolean {
  return Boolean(getAuthToken());
}
