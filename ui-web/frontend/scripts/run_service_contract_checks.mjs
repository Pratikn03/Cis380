import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

function read(relativePath) {
  return readFileSync(path.join(root, relativePath), "utf-8");
}

function assertContains(source, needle, message) {
  if (!source.includes(needle)) {
    throw new Error(message);
  }
}

function run() {
  const apiSource = read("src/services/api.ts");
  const endpointsSource = read("src/services/endpoints.ts");

  assertContains(
    apiSource,
    "config.headers.Authorization = `Bearer ${token}`",
    "api.ts must inject Authorization header from AUTH_TOKEN.",
  );

  const endpointContracts = [
    'api.post("/api/chat"',
    'api.post("/api/risk/analyze"',
    'api.post("/api/fraud"',
    'api.post("/api/cyber"',
    'api.post("/api/behavior"',
    'api.post("/api/rag/ask"',
    'api.get("/api/rag/status"',
  ];

  for (const contract of endpointContracts) {
    assertContains(
      endpointsSource,
      contract,
      `endpoints.ts missing required contract: ${contract}`,
    );
  }

  console.log("legacy-service-contracts: PASS");
}

try {
  run();
} catch (error) {
  console.error("legacy-service-contracts: FAIL");
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
}
