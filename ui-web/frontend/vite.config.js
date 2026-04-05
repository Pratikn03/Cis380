import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig(function (_a) {
    var mode = _a.mode;
    var env = loadEnv(mode, process.cwd(), "");
    // Use relative base path "./" so it works from any location
    // This works for both GitHub Pages and local /ui/ serving
    var base = env.VITE_BASE_PATH || "./";
    return {
        base: base,
        plugins: [react()],
        build: {
            outDir: "dist",
            assetsDir: "assets",
        },
    };
});
