/** Where the API answers: its address plus the version. A breaking API change
 * becomes /api/v2 beside this, so old pages keep working while new ones move.
 * Server-side code may reach the API by a private address (INTERNAL_API_URL, e.g.
 * between containers); the browser always uses the public NEXT_PUBLIC_API_URL. */
const origin =
  (typeof window === "undefined" && process.env.INTERNAL_API_URL) || process.env.NEXT_PUBLIC_API_URL || "";

export const API_BASE = `${origin.replace(/\/+$/, "")}/api/v1`;
