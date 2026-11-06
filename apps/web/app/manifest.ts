import type { MetadataRoute } from "next";

/** What a phone needs to offer "Add to Home Screen" and open the app like an app (no browser bars). */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Uraan AI",
    short_name: "Uraan AI",
    description: "Pick a career, get a personalised roadmap, and learn it step by step with an AI mentor.",
    start_url: "/dashboard",
    scope: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#0b0a1a",
    theme_color: "#7c3aed",
    categories: ["education", "productivity"],
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      { src: "/icons/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
    shortcuts: [
      { name: "Continue learning", url: "/dashboard" },
      { name: "My roadmaps", url: "/roadmaps" },
      { name: "AI mentor", url: "/mentor" },
    ],
  };
}
