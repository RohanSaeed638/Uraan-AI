"use client";

import { useTranslations } from "next-intl";

import { Input } from "@/components/ui/input";

import NavigationButtons from "@/components/onboarding/NavigationButtons";
import OnboardingCard from "@/components/onboarding/OnboardingCard";

import { StepProps } from "../types";

export default function ProfileStep({
  data,
  updateData,
  next,
  previous,
}: StepProps) {
  const t = useTranslations("onboarding.profile");

  return (
    <OnboardingCard
      title={t("title")}
      subtitle={t("subtitle")}
    >
      <Input
        placeholder={t("name")}
        value={data.full_name}
        onChange={(e) =>
          updateData({
            full_name: e.target.value,
          })
        }
      />

      <NavigationButtons
        showBack
        onBack={previous}
        onNext={next}
      />
    </OnboardingCard>
  );
}