import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      { find: "@", replacement: path.resolve(__dirname) },
      // The workspace has two copies of React (here and at the repository root). Libraries
      // load the root one, so the app's code must too, or hooks fail with "dispatcher is null".
      { find: /^react$/, replacement: path.resolve(__dirname, "../../node_modules/react") },
      { find: /^react\/(.*)$/, replacement: path.resolve(__dirname, "../../node_modules/react") + "/$1" },
      { find: /^react-dom$/, replacement: path.resolve(__dirname, "../../node_modules/react-dom") },
      { find: /^react-dom\/(.*)$/, replacement: path.resolve(__dirname, "../../node_modules/react-dom") + "/$1" },
    ],
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/unit/**/*.test.{ts,tsx}"],
    css: false,
    // Modules that build a Supabase client when imported need some values; these are never contacted.
    env: {
      NEXT_PUBLIC_SUPABASE_URL: "http://localhost:54321",
      NEXT_PUBLIC_SUPABASE_ANON_KEY: "test-key",
      NEXT_PUBLIC_API_URL: "http://localhost:8000",
    },
  },
});
