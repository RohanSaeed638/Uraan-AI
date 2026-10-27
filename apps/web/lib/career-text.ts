/**
 * Career names, descriptions, categories and skills live in the API's
 * catalogue (data/careers.json) in English. The same text is in the message
 * files under `catalog` (scripts/sync_career_messages.py), so it reads in the
 * learner's language; anything without a translation keeps the catalogue text.
 */

/** "Git and GitHub" -> "git_and_github". The same rule as the sync script. */
export function catalogKey(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 80)
    .replace(/_+$/, "");
}

/** What `useTranslations("catalog")` / `getTranslations("catalog")` returns. */
interface CatalogT {
  (key: string): string;
  has: (key: string) => boolean;
}

export function careerText(t: CatalogT) {
  const pick = (key: string, fallback: string) => (t.has(key) ? t(key) : fallback);

  return {
    name: (slug: string, fallback: string) => pick(`careers.${slug}.name`, fallback),
    description: (slug: string, fallback: string) =>
      pick(`careers.${slug}.description`, fallback),
    category: (text: string) => pick(`categories.${catalogKey(text)}`, text),
    skill: (text: string) => pick(`skills.${catalogKey(text)}`, text),
  };
}
