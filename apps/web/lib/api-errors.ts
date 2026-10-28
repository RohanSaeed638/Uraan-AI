/**
 * The API writes its messages in English and sends an `error_code` made from
 * them (apps/api/app/core/error_codes.py). The web app looks the code up in
 * `errors.<code>` of the message files so learners read their own language,
 * and falls back to the English text when there is no translation.
 */

/** "Profile not found" -> "profile_not_found". The same rule as the API's. */
export function errorCode(message: string): string {
  return message
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 80)
    .replace(/_+$/, "");
}

type Lookup = (code: string) => string | null;

// Set once the messages are known (see ErrorTranslator); before that, and on
// the server, messages stay in English.
let lookup: Lookup | null = null;

export function setErrorLookup(next: Lookup | null) {
  lookup = next;
}

/** An API message in the learner's language, or the message itself. */
export function translateApiMessage(message: string): string {
  return lookup?.(errorCode(message)) ?? message;
}
