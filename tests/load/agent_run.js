// k6 smoke load test for the agent endpoint.
//
// Usage (against `make dev`):
//   k6 run -e BASE_URL=http://localhost:8000 tests/load/agent_run.js
//
// Stages:
//   1) Ramp up to 5 VUs over 30s (steady warm).
//   2) Hold 5 VUs for 60s (where p95 must stay < 4s with prompt cache warm).
//   3) Burst to 20 VUs for 30s to confirm the rate-limit middleware
//      starts shedding rather than queuing forever.
//   4) Ramp down.
//
// Pass criteria (k6 thresholds):
//   * 99% of requests return 200 or 429 (no 5xx).
//   * p95 of successful requests < 4s during the steady phase.
//   * The rate of failures (5xx) stays under 1%.

import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Rate } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const TOKEN = __ENV.AUTH_TOKEN || "";

const successLatency = new Trend("agent_success_latency");
const errorRate = new Rate("agent_error_rate");

export const options = {
  stages: [
    { duration: "30s", target: 5 },
    { duration: "60s", target: 5 },
    { duration: "30s", target: 20 },
    { duration: "20s", target: 0 },
  ],
  thresholds: {
    // 99% of responses are not 5xx — 429 is allowed during the burst.
    "http_req_failed": ["rate<0.01"],
    // p95 latency on successful requests must stay under 4s in steady state.
    "agent_success_latency": ["p(95)<4000"],
    "agent_error_rate": ["rate<0.05"],
  },
};

const SAMPLE_QUERIES = [
  "is this transaction fraudulent: $5000 from RU",
  "user accessed 200 files outside normal hours — score behaviour",
  "lookup the password rotation policy",
  "recommend a laptop for ML training",
  "score the cyber risk for failed logins from 5 different countries",
];

export default function () {
  const message = SAMPLE_QUERIES[Math.floor(Math.random() * SAMPLE_QUERIES.length)];
  const params = {
    headers: TOKEN ? { Authorization: `Bearer ${TOKEN}` } : undefined,
    timeout: "30s",
  };
  const body = { message };
  const res = http.post(
    `${BASE_URL}/api/v1/agent/run`,
    Object.entries(body).map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`).join("&"),
    {
      ...params,
      headers: {
        ...(params.headers || {}),
        "Content-Type": "application/x-www-form-urlencoded",
      },
    },
  );

  const ok = check(res, {
    "status is 200": (r) => r.status === 200,
    "received SSE": (r) => typeof r.body === "string" && r.body.includes("event: trace_start"),
  });

  if (res.status === 200) {
    successLatency.add(res.timings.duration);
  }
  errorRate.add(!ok);

  sleep(1 + Math.random() * 2);
}
