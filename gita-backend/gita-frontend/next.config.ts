import path from "node:path";
import { fileURLToPath } from "node:url";
import type { NextConfig } from "next";

/**
 * Monorepo-ish root (`gita-backend/`: this app + `../backend`).
 * Must be **above** the Next app dir — same-dir `outputFileTracingRoot` breaks Turbopack
 * (`distDirRoot should not navigate out of the projectPath`).
 */
const nextAppDir = path.dirname(fileURLToPath(import.meta.url));
const tracingRoot = path.join(nextAppDir, "..");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: tracingRoot,
};

export default nextConfig;
