"use client";

import OnboardingCard from "@/components/onboarding/OnboardingCard";
import NavigationButtons from "@/components/onboarding/NavigationButtons";
import TargetIllustration from "@/components/illustrations/TargetIllustration";

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
      illustration={<TargetIllustration />}
    >
      <div className="space-y-8">
        <div className="text-center">
          <h2 className="text-5xl font-bold text-brand-violet">
            {data.target_duration}
          </h2>

          <p className="mt-2 text-muted-foreground">Months</p>
        </div>

        <Slider
          value={[data.target_duration]}
          min={3}
          max={24}
          step={3}
          onValueChange={(value) =>
            updateData({
              target_duration: Array.isArray(value) ? value[0] : value,
            })
          }
        />

        <div className="grid grid-cols-3 gap-3">
          {DURATIONS.map((duration) => (
            <Button
              key={duration}
              variant={duration === data.target_duration ? "default" : "outline"}
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

      <NavigationButtons showBack onBack={previous} onNext={next} />
    </OnboardingCard>
  );
}
