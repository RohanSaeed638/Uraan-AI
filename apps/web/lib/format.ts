/**
 * Dates for components that are rendered on the server and then hydrated in
 * the browser. A fixed timezone gives the same text in both places; the
 * browser's own locale would not, so the app's language is passed in.
 */

/** Roman Urdu is Latin script, so dates and numbers use English forms; the
 * `ur` formats would print Urdu-script month names. */
export const intlLocale = (locale: string) =>
  locale === "ur-Latn" ? "en-GB" : locale;

export function formatDate(
  value: string | number | Date,
  options: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
  },
  locale = "en"
): string {
  return new Date(value).toLocaleDateString(intlLocale(locale === "en" ? "en-US" : locale), {
    timeZone: "UTC",
    ...options,
  });
}

export function formatNumber(value: number, locale = "en"): string {
  return value.toLocaleString(intlLocale(locale === "en" ? "en-US" : locale));
}
