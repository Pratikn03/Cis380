import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

const threshold = Number.parseInt(process.env.NEXT_THRESHOLD ?? process.env.VITEST_COVERAGE_THRESHOLD ?? "95", 10);
const rootDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    pool: "forks",
    poolOptions: {
      forks: {
        minForks: 1,
        maxForks: 1,
      },
    },
    fileParallelism: false,
    testTimeout: 15000,
    hookTimeout: 15000,
    coverage: {
      provider: "v8",
      reporter: ["text", "json-summary", "lcov"],
      reportsDirectory: "../../reports/coverage/next",
      include: [
        "src/lib/auth.ts",
        "src/lib/gateway-graphql.ts",
      ],
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
