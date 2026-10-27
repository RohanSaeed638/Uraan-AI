"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { toast } from "sonner";

import { setLocaleCookie } from "@/app/actions/locale";
import { LOCALES, LOCALE_LABELS, Locale, isLocale } from "@/i18n/config";
import { patchProfile } from "@/lib/api/profile";

import FilterChips from "@/components/shared/FilterChips";

/** Picks the app's language. Saved on the account too when `signedIn`, so it
 * follows the learner to another device. */
export default function LanguageSwitcher({ signedIn = true }: { signedIn?: boolean }) {
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

  return (
    <FilterChips
      label={t("label")}
      value={isLocale(current) ? current : "en"}
      onChange={choose}
      options={LOCALES.map((value) => ({ value, label: LOCALE_LABELS[value] }))}
    />
  );
}
