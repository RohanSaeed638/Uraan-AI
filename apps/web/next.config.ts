import path from "node:path";
import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./i18n/request.ts");

const nextConfig: NextConfig = {
  // A production build for testing goes in its own folder (NEXT_DIST_DIR=.next-test),
  // so it never overwrites the `next dev` files in .next while you are working.
  distDir: process.env.NEXT_DIST_DIR || ".next",
  // The Docker image runs the self-contained "standalone" build (NEXT_OUTPUT=standalone);
  // the repository root is the tracing root because this app lives in a workspace.
  ...(process.env.NEXT_OUTPUT === "standalone"
    ? { output: "standalone" as const, outputFileTracingRoot: path.join(__dirname, "../..") }
    : {}),
};

export default withNextIntl(nextConfig);
