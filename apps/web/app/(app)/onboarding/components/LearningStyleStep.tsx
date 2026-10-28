"use client";

import { BookOpen, Video, Code2 } from "lucide-react";
import OnboardingCard from "@/components/onboarding/OnboardingCard";
import OptionCard from "@/components/onboarding/OptionCard";
import NavigationButtons from "@/components/onboarding/NavigationButtons";
import { useTranslations } from "next-intl";
import { StepProps, LearningStyle } from "../types";

const learningStyles = [
  { value: "reading" as LearningStyle, icon: BookOpen },
  { value: "reading_video" as LearningStyle, icon: Video },
  { value: "reading_video_project" as LearningStyle, icon: Code2 },
];

export default function LearningStyleStep({
  data,
  updateData,
  next,
  previous,
}: StepProps) {
  const t = useTranslations("onboarding.style");

  return (
    <OnboardingCard
      title={t("title")}
      subtitle={t("subtitle")}
    >
      <div className="grid gap-4">
        {learningStyles.map((style) => (
          <OptionCard
            key={style.value}
            icon={<style.icon size={18} />}
            title={t(style.value)}
            description={t(`${style.value}Text`)}
            selected={data.learning_style === style.value}
            onClick={() =>
              updateData({
                learning_style: style.value,
              })
            }
          />
        ))}
      </div>

      <NavigationButtons
        showBack
        onBack={previous}
        onNext={next}
        loading={!data.learning_style}
      />
    </OnboardingCard>
  );
}
