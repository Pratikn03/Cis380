import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig(function (_a) {
    var mode = _a.mode;
    var env = loadEnv(mode, process.cwd(), "");
    // For GitHub Pages: use /Cis380/ as base path (repo name)
    // For local: use / or /ui/
    var base = env.VITE_BASE_PATH || (mode === "production" ? "/Cis380/" : "/");
    return {
        base: base,
        plugins: [react()],
        build: {
            outDir: "dist",
            assetsDir: "assets",
        },
    };
});
