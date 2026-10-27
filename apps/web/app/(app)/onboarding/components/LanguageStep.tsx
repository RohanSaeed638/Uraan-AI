"use client";

import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";

import { setLocaleCookie } from "@/app/actions/locale";
import { LANGUAGES } from "../constants";

import OptionCard from "@/components/onboarding/OptionCard";
import NavigationButtons from "@/components/onboarding/NavigationButtons";
import OnboardingCard from "@/components/onboarding/OnboardingCard";

import { StepProps } from "../types";

export default function LanguageStep({
  data,
  updateData,
  next,
  previous,
}: StepProps) {
  const t = useTranslations("onboarding.language");
  const router = useRouter();
  const current = useLocale();

  // The rest of the onboarding switches to the chosen language at once.
  async function choose(value: string) {
    updateData({ language: value });

    if (value !== current) {
      await setLocaleCookie(value);
      router.refresh();
    }
  }

  return (
    <OnboardingCard
      title={t("title")}
      subtitle={t("subtitle")}
    >
      <div className="grid gap-4">

        {LANGUAGES.map((lang) => (
          <OptionCard
            key={lang.value}
            title={lang.label}
            selected={
              data.language === lang.value
            }
            onClick={() => choose(lang.value)}
          />
        ))}

      </div>

      <NavigationButtons
        showBack
        onBack={previous}
        onNext={next}
      />
    </OnboardingCard>
  );
}