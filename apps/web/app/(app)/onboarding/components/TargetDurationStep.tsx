"use client";

import OnboardingCard from "@/components/onboarding/OnboardingCard";
import NavigationButtons from "@/components/onboarding/NavigationButtons";
import TargetIllustration from "@/components/illustrations/TargetIllustration";

import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";

import { useTranslations } from "next-intl";

import { StepProps } from "../types";

const DURATIONS = [3, 6, 9, 12, 18, 24];

export default function TargetDurationStep({
  data,
  updateData,
  next,
  previous,
}: StepProps) {
  const t = useTranslations("onboarding.duration");

  return (
    <OnboardingCard
      title={t("title")}
      subtitle={t("subtitle")}
      illustration={<TargetIllustration />}
    >
      <div className="space-y-8">
        <div className="text-center">
          <h2 className="text-5xl font-bold text-brand-violet">
            {data.target_duration}
          </h2>

          <p className="mt-2 text-muted-foreground">{t("months")}</p>
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
              {t("preset", { count: duration })}
            </Button>
          ))}
        </div>
      </div>

      <NavigationButtons showBack onBack={previous} onNext={next} />
    </OnboardingCard>
  );
}
