import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Produces a self-contained .next/standalone directory for Docker.
  // Does not affect `next dev` or local `next build`.
  output: "standalone",
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
