/**
 * Dates for components that are rendered on the server and then hydrated in
 * the browser. A fixed locale and timezone give the same text in both places;
 * the browser's own locale would not, and React would have to re-render.
 */
export function formatDate(
  value: string | number | Date,
  options: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
  }
): string {
  return new Date(value).toLocaleDateString("en-US", {
    timeZone: "UTC",
    ...options,
  });
}
