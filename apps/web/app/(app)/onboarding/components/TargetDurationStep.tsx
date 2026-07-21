"use client";

import OnboardingCard from "@/components/onboarding/OnboardingCard";
import NavigationButtons from "@/components/onboarding/NavigationButtons";

import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";

import { StepProps } from "../types";

const DURATIONS = [3, 6, 9, 12, 18, 24];

export default function TargetDurationStep({
  data,
  updateData,
  next,
  previous,
}: StepProps) {
  return (
    <OnboardingCard
      title="When do you want to become job ready?"
      subtitle="Choose a realistic goal."
    >
      <div className="space-y-8">

        <div className="text-center">
          <h2 className="text-5xl font-bold text-purple-600">
            {data.target_duration}
          </h2>

          <p className="mt-2 text-muted-foreground">
            Months
          </p>
        </div>

        <Slider
          value={[data.target_duration]}
          min={3}
          max={24}
          step={3}
          onValueChange={(value) =>
            updateData({
              target_duration: value[0],
            })
          }
        />

        <div className="grid grid-cols-3 gap-3">
          {DURATIONS.map((duration) => (
            <Button
              key={duration}
              variant={
                duration === data.target_duration
                  ? "default"
                  : "outline"
              }
              onClick={() =>
                updateData({
                  target_duration: duration,
                })
              }
            >
              {duration} Months
            </Button>
          ))}
        </div>

      </div>

      <NavigationButtons
        showBack
        onBack={previous}
        onNext={next}
      />
    </OnboardingCard>
  );
}