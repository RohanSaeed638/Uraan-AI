"use client";

import { BookOpen, Video, Code2 } from "lucide-react";
import OnboardingCard from "@/components/onboarding/OnboardingCard";
import OptionCard from "@/components/onboarding/OptionCard";
import NavigationButtons from "@/components/onboarding/NavigationButtons";
import { StepProps, LearningStyle } from "../types";

const learningStyles = [
  {
    value: "READING" as LearningStyle,
    icon: BookOpen,
    title: "Reading",
    description: "Text-based learning with structured content.",
  },
  {
    value: "READING_VIDEO" as LearningStyle,
    icon: Video,
    title: "Reading + Videos",
    description: "Reading plus video tutorials and guides.",
  },
  {
    value: "READING_VIDEO_PROJECT" as LearningStyle,
    icon: Code2,
    title: "Reading + Videos + Projects",
    description: "Hands-on projects and real-world practice.",
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
      title="Choose your learning style"
      subtitle="Select how you prefer to learn. Each option builds on the last."
    >
      <div className="grid gap-4">
        {learningStyles.map((style) => (
          <OptionCard
            key={style.value}
            icon={<style.icon size={18} />}
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
