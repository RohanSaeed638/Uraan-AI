import { cookies } from "next/headers";
import { getRequestConfig } from "next-intl/server";

import { DEFAULT_LOCALE, LOCALE_COOKIE, WORDING_COOKIE, isLocale } from "./config";

type Messages = { [key: string]: string | Messages };

/** `over` on top of `base`, key by key, so a missing translation shows the English. */
function withFallback(base: Messages, over: Messages): Messages {
  const out: Messages = { ...base };

  for (const [key, value] of Object.entries(over)) {
    const current = out[key];

    out[key] =
      typeof value === "object" && typeof current === "object"
        ? withFallback(current, value)
        : value;
  }

  return out;
}

// No URL prefixes: the locale comes from the NEXT_LOCALE cookie.
export default getRequestConfig(async () => {
  const jar = await cookies();
  const stored = jar.get(LOCALE_COOKIE)?.value;
  const locale = isLocale(stored) ? stored : DEFAULT_LOCALE;

  const english = (await import("../messages/en.json")).default as Messages;
  let messages =
    locale === DEFAULT_LOCALE
      ? english
      : withFallback(
          english,
          (await import(`../messages/${locale}.json`)).default as Messages
        );

  // Game wording: a small file of replacement words for this language.
  if (jar.get(WORDING_COOKIE)?.value === "gamified") {
    const overlay = (await import(`../messages/gamified/${locale}.json`).catch(() => null))
      ?.default as Messages | undefined;

    if (overlay) messages = withFallback(messages, overlay);
  }

  return { locale, messages };
});
