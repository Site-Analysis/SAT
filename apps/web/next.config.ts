import type { NextConfig } from "next";
import path from "path";
import { fileURLToPath } from "url";

const appDir = path.dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  reactStrictMode: false,
  // Monorepo lives under SAT/; avoid picking up a stray lockfile in $HOME.
  outputFileTracingRoot: path.join(appDir, "../.."),
};

export default nextConfig;
