import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

const threshold = Number.parseInt(process.env.LEGACY_THRESHOLD ?? process.env.VITEST_COVERAGE_THRESHOLD ?? "95", 10);
const rootDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  test: {
    environment: "node",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/services/api.test.ts", "src/services/endpoints.test.ts"],
    pool: "forks",
    poolOptions: {
      forks: {
        minForks: 1,
        maxForks: 1,
      },
    },
    fileParallelism: false,
    testTimeout: 10000,
    hookTimeout: 10000,
    coverage: {
      provider: "v8",
      reporter: ["text", "json-summary", "lcov"],
      reportsDirectory: "../../reports/coverage/legacy",
      include: ["src/services/api.ts", "src/services/endpoints.ts"],
      exclude: ["src/**/*.d.ts", "src/test/**"],
      thresholds: {
        lines: threshold,
        functions: threshold,
        branches: threshold,
        statements: threshold,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(rootDir, "./src"),
    },
  },
});
