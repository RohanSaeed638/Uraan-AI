"use client";

import OnboardingCard from "@/components/onboarding/OnboardingCard";
import OptionCard from "@/components/onboarding/OptionCard";
import NavigationButtons from "@/components/onboarding/NavigationButtons";
import { StepProps, LearningStyle } from "../types";

const learningStyles = [
  {
    value: "videos" as LearningStyle,
    title: "🎥 Videos",
    description: "I learn best through video tutorials.",
  },
  {
    value: "reading" as LearningStyle,
    title: "📚 Reading",
    description: "I prefer books and written guides.",
  },
  {
    value: "projects" as LearningStyle,
    title: "💻 Projects",
    description: "I learn by building real applications.",
  },
  {
    value: "mixed" as LearningStyle,
    title: "🎯 Mixed",
    description: "A combination of videos, reading and projects.",
  },
];

export default function LearningStyleStep({
  data,
  updateData,
  next,
  previous,
}: StepProps) {
  return (
    <OnboardingCard
      title="How do you prefer learning?"
      subtitle="We'll customize the roadmap to match your style."
    >
      <div className="grid gap-4">
        {learningStyles.map((style) => (
          <OptionCard
            key={style.value}
            title={style.title}
            description={style.description}
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