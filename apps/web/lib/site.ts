/** Public facts about the site, set at build time (NEXT_PUBLIC_*). */

/** Where learners write for help, and for data requests (see docs/deployment.md). */
export const CONTACT_EMAIL = (process.env.NEXT_PUBLIC_CONTACT_EMAIL ?? "").trim();

/** When the Terms and the Privacy Policy last changed. Update it with the text. */
export const LEGAL_UPDATED = "1 November 2026";
