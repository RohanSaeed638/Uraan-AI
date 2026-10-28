/** Shared by server and client code: nothing here may import next/headers. */
export const LOCALES = ["en", "ur", "ur-Latn"] as const;

export type Locale = (typeof LOCALES)[number];

export const DEFAULT_LOCALE: Locale = "en";
export const LOCALE_COOKIE = "NEXT_LOCALE";

/** Each language in its own words, so a learner can find theirs. */
export const LOCALE_LABELS: Record<Locale, string> = {
  en: "English",
  ur: "اردو",
  "ur-Latn": "Roman Urdu",
};

export const isLocale = (value: unknown): value is Locale =>
  typeof value === "string" && (LOCALES as readonly string[]).includes(value);

/** Urdu in Urdu script reads right to left; Roman Urdu is Latin and does not. */
export const isRtl = (locale: string) => locale === "ur";

/** Plain words ("Tasks") or game words ("Missions"): an overlay of messages. */
export const WORDINGS = ["classic", "gamified"] as const;

export type Wording = (typeof WORDINGS)[number];

export const WORDING_COOKIE = "NEXT_WORDING";

export const isWording = (value: unknown): value is Wording =>
  typeof value === "string" && (WORDINGS as readonly string[]).includes(value);
