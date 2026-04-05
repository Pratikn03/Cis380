export type AuthMode = "disabled" | "jwt";

export function getGraphqlHttpUrl(): string {
  return process.env.NEXT_PUBLIC_GRAPHQL_HTTP ?? "http://localhost:8081/graphql";
}

export function getGraphqlWsUrl(): string {
  return process.env.NEXT_PUBLIC_GRAPHQL_WS ?? "ws://localhost:8081/graphql";
}

export function getAuthMode(): AuthMode {
  const raw = (process.env.NEXT_PUBLIC_AUTH_MODE ?? "").trim().toLowerCase();
  const isProduction = process.env.NODE_ENV === "production";

  if (raw === "jwt") {
    return "jwt";
  }

  if (raw === "disabled") {
    return isProduction ? "jwt" : "disabled";
  }

  return isProduction ? "jwt" : "disabled";
}

export function authModeLabel(mode: AuthMode): string {
  return mode === "jwt" ? "JWT" : "Disabled";
}
