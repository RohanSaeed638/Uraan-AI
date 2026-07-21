"use client";

import OnboardingCard from "@/components/onboarding/OnboardingCard";
import OptionCard from "@/components/onboarding/OptionCard";
import NavigationButtons from "@/components/onboarding/NavigationButtons";

import { StepProps, SkillLevel } from "../types";

const skillLevels = [
  {
    value: "beginner" as SkillLevel,
    title: "🌱 Beginner",
    description: "I'm completely new to this career.",
  },
  {
    value: "intermediate" as SkillLevel,
    title: "🔥 Intermediate",
    description: "I know the basics and have built a few projects.",
  },
  {
    value: "advanced" as SkillLevel,
    title: "🚀 Advanced",
    description: "I have experience and want to level up.",
  },
];

export default function SkillLevelStep({
  data,
  updateData,
  next,
  previous,
}: StepProps) {
  return (
    <OnboardingCard
      title="What's your current skill level?"
      subtitle="This helps us generate the right roadmap."
    >
      <div className="grid gap-4">
        {skillLevels.map((level) => (
          <OptionCard
            key={level.value}
            title={level.title}
            description={level.description}
            selected={data.skill_level === level.value}
            onClick={() =>
              updateData({
                skill_level: level.value,
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