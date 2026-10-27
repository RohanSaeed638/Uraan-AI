"use client";

import { useTranslations } from "next-intl";

import OnboardingCard from "@/components/onboarding/OnboardingCard";
import NavigationButtons from "@/components/onboarding/NavigationButtons";
import OptionCard from "@/components/onboarding/OptionCard";

import { GOAL_TYPES, PACES, STUDY_HOURS } from "@/lib/profile-options";

import { StepProps } from "../types";

export default function YourPlanStep({
  data,
  updateData,
  next,
  previous,
}: StepProps) {
  const t = useTranslations("onboarding.plan");
  const o = useTranslations("options");

  return (
    <OnboardingCard title={t("title")} subtitle={t("subtitle")}>
      <div className="space-y-8">
        <div className="space-y-3">
          <p className="text-sm font-medium">{t("goal")}</p>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {GOAL_TYPES.map((value) => (
              <OptionCard
                key={value}
                title={o(`goal_type.${value}`)}
                selected={data.goal_type === value}
                onClick={() => updateData({ goal_type: value })}
              />
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <p className="text-sm font-medium">{t("hours")}</p>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {STUDY_HOURS.map((value) => (
              <OptionCard
                key={value}
                title={o(`study_hours.${value}`)}
                selected={data.preferred_study_hours === value}
                onClick={() => updateData({ preferred_study_hours: value })}
              />
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <p className="text-sm font-medium">{t("pace")}</p>

          <div className="grid gap-3 sm:grid-cols-3">
            {PACES.map((value) => (
              <OptionCard
                key={value}
                title={o(`pace.${value}`)}
                description={t(`paceHint.${value}`)}
                selected={data.learning_pace === value}
                onClick={() => updateData({ learning_pace: value })}
              />
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <p className="text-sm font-medium">{t("weekend")}</p>

          <div className="grid gap-3 sm:grid-cols-2">
            <OptionCard
              title={t("weekendYes")}
              selected={data.weekend_study === true}
              onClick={() => updateData({ weekend_study: true })}
            />

            <OptionCard
              title={t("weekendNo")}
              selected={data.weekend_study === false}
              onClick={() => updateData({ weekend_study: false })}
            />
          </div>
        </div>
      </div>

      <NavigationButtons
        showBack
        onBack={previous}
        onNext={next}
        nextLabel={t("continue")}
      />
    </OnboardingCard>
  );
}
