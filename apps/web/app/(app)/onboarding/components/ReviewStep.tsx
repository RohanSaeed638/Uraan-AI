"use client";

import OnboardingCard from "@/components/onboarding/OnboardingCard";
import NavigationButtons from "@/components/onboarding/NavigationButtons";
import SummaryCard from "@/components/onboarding/SummaryCard";

import { StepProps } from "../types";

export default function ReviewStep({
  data,
  previous,
  next: submit,
}: StepProps) {
  return (
    <OnboardingCard
      title="Review your roadmap"
      subtitle="Everything look good?"
    >
      <div className="grid grid-cols-2 gap-4">

        <SummaryCard
          label="Name"
          value={data.full_name}
        />

        <SummaryCard
          label="Language"
          value={data.language}
        />

        <SummaryCard
          label="Career"
          value={data.career_slug}
        />

        <SummaryCard
          label="Skill Level"
          value={data.skill_level}
        />

        <SummaryCard
          label="Learning Style"
          value={data.learning_style}
        />

        <SummaryCard
          label="Daily Hours"
          value={`${data.daily_hours} hrs`}
        />

        <SummaryCard
          label="Goal"
          value={`${data.target_duration} months`}
        />

      </div>

      <NavigationButtons
        showBack
        onBack={previous}
        onNext={submit}
        nextLabel="Generate My Roadmap 🚀"
      />
    </OnboardingCard>
  );
}