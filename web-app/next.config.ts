import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // ─── Stage 12: Docker-optimized standalone output ────────────────────────
  // Produces .next/standalone — a self-contained server.js runner.
  // Required by the multi-stage Dockerfile.
  output: "standalone",

  async rewrites() {
    // BACKEND_URL is set to the internal Docker service name (e.g. http://backend:8000)
    // when running inside Docker Compose, and falls back to localhost for local dev.
    const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: "/ws/:path*",
        destination: `${backendUrl}/ws/:path*`,
      },
    ];
  },
  experimental: {
    // allow server actions and edge runtime if needed later
  },
};

export default nextConfig;

