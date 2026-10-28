"use client";

import OnboardingCard from "@/components/onboarding/OnboardingCard";
import OptionCard from "@/components/onboarding/OptionCard";
import NavigationButtons from "@/components/onboarding/NavigationButtons";

import { useTranslations } from "next-intl";

import { StepProps, SkillLevel } from "../types";

const skillLevels = ["beginner", "intermediate", "advanced"] as SkillLevel[];

export default function SkillLevelStep({
  data,
  updateData,
  next,
  previous,
}: StepProps) {
  const t = useTranslations("onboarding.skill");

  return (
    <OnboardingCard
      title={t("title")}
      subtitle={t("subtitle")}
    >
      <div className="grid gap-4">
        {skillLevels.map((level) => (
          <OptionCard
            key={level}
            title={t(level)}
            description={t(`${level}Text`)}
            selected={data.skill_level === level}
            onClick={() =>
              updateData({
                skill_level: level,
              })
            }
          />
        ))}
      </div>

      <NavigationButtons
        showBack
        onBack={previous}
        onNext={next}
        loading={!data.skill_level}
      />
    </OnboardingCard>
  );
}