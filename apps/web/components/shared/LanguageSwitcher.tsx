"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Globe } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { toast } from "sonner";

import { setLocaleCookie } from "@/app/actions/locale";
import { LOCALES, LOCALE_LABELS, Locale, isLocale } from "@/i18n/config";
import { patchProfile } from "@/lib/api/profile";

import FilterChips from "@/components/shared/FilterChips";

/** Picks the app's language. Saved on the account too when `signedIn`, so it
 * follows the learner to another device. */
export default function LanguageSwitcher({
  signedIn = true,
  compact = false,
}: {
  signedIn?: boolean;
  /** A small drop-down instead of the row of buttons, for narrow screens. */
  compact?: boolean;
}) {
  const t = useTranslations("language");
  const router = useRouter();
  const current = useLocale();
  const [busy, setBusy] = useState(false);

  async function choose(next: Locale) {
    if (busy || next === current) return;

    setBusy(true);

    try {
      await setLocaleCookie(next);

      if (signedIn) {
        // The page still switches if the account could not be updated.
        await patchProfile({ language: next }).catch(() =>
          toast.error(t("saveFailed"))
        );
      }

      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  if (compact) {
    // On a phone it is just a globe button (the real drop-down sits invisibly on top of it, so a tap
    // opens the language list); from the small breakpoint up it shows the current language.
    return (
      <label className="relative inline-flex items-center">
        <Globe size={16} aria-hidden className="pointer-events-none absolute start-[0.6rem] text-muted-foreground sm:start-3" />
        <select
          aria-label={t("label")}
          value={isLocale(current) ? current : "en"}
          disabled={busy}
          onChange={(event) => choose(event.target.value as Locale)}
          className="h-9 w-9 cursor-pointer appearance-none rounded-full border border-border bg-background text-sm font-medium text-transparent outline-none focus-visible:ring-3 focus-visible:ring-ring/30 sm:w-auto sm:ps-9 sm:pe-3 sm:text-foreground"
        >
          {LOCALES.map((value) => (
            <option key={value} value={value} className="bg-background text-foreground">
              {LOCALE_LABELS[value]}
            </option>
          ))}
        </select>
      </label>
    );
  }

  return (
    <FilterChips
      label={t("label")}
      value={isLocale(current) ? current : "en"}
      onChange={choose}
      options={LOCALES.map((value) => ({ value, label: LOCALE_LABELS[value] }))}
    />
  );
}
