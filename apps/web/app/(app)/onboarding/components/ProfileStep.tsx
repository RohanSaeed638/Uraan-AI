"use client";

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
  return (
    <OnboardingCard
      title="Tell us about yourself"
      subtitle="We'll personalize everything."
    >
      <Input
        placeholder="Your Full Name"
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