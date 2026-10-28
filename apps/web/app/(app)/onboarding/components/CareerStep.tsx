"use client";

import { useTranslations } from "next-intl";

import { careerIcon, useCareerOptions } from "@/lib/careers";

import OptionCard from "@/components/onboarding/OptionCard";
import NavigationButtons from "@/components/onboarding/NavigationButtons";
import OnboardingCard from "@/components/onboarding/OnboardingCard";

import { StepProps } from "../types";

export default function CareerStep({
  data,
  updateData,
  next,
  previous,
}: StepProps) {
  const t = useTranslations("onboarding.career");
  const { options } = useCareerOptions();

  return (
    <OnboardingCard title={t("title")} subtitle={t("subtitle")}>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {options.map((career) => (
            <OptionCard
              key={career.value}
              title={career.label}
              description={career.description}
              icon={careerIcon(career.icon, 24)}
              selected={data.career_slug === career.value}
              onClick={() => updateData({ career_slug: career.value })}
            />
        ))}
      </div>

      <p className="mt-4 text-sm text-muted-foreground">{t("notSure")}</p>

      <NavigationButtons
        showBack
        onBack={previous}
        onNext={data.career_slug ? next : () => {}}
      />
    </OnboardingCard>
  );
}
