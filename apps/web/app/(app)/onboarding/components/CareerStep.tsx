"use client";

import { careers } from "@/lib/constants/careers";

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
  return (
    <OnboardingCard
      title="Choose your dream career"
      subtitle="We'll build a roadmap for it."
    >
      <div className="grid grid-cols-2 gap-4">

        {careers.map((career) => {
          const Icon = career.icon;

          return (
            <OptionCard
              key={career.value}
              title={career.label}
              description={
                career.description
              }
              icon={<Icon size={24} />}
              selected={
                data.career_slug ===
                career.value
              }
              onClick={() =>
                updateData({
                  career_slug:
                    career.value,
                })
              }
            />
          );
        })}
      </div>

      <NavigationButtons
        showBack
        onBack={previous}
        onNext={next}
      />
    </OnboardingCard>
  );
}