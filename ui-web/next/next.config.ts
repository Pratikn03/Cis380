import type { NextConfig } from "next";

const rawBasePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
const normalizedBasePath =
  rawBasePath === "/" ? "" : rawBasePath.replace(/\/$/, "");
const staticExport = process.env.STATIC_EXPORT === "true";

const nextConfig: NextConfig = {
  output: staticExport ? "export" : undefined,
  trailingSlash: staticExport,
  images: staticExport ? { unoptimized: true } : undefined,
  basePath: normalizedBasePath,
  assetPrefix: normalizedBasePath || undefined,
  allowedDevOrigins: [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.4.94:3000",
  ],
};

export default nextConfig;
