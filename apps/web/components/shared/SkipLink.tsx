import { getTranslations } from "next-intl/server";

/** The first thing a keyboard user tabs to: jumps past the menu to the page. */
export default async function SkipLink() {
  const t = await getTranslations("a11y");

  return (
    <a
      href="#main"
      className="sr-only z-[100] rounded-full bg-brand-gold px-5 py-2.5 text-sm font-semibold text-[#241a05] focus:not-sr-only focus:fixed focus:start-4 focus:top-4"
    >
      {t("skip")}
    </a>
  );
}
