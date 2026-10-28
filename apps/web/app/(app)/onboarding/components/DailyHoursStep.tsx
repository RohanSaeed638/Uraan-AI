"use client";

import OnboardingCard from "@/components/onboarding/OnboardingCard";
import NavigationButtons from "@/components/onboarding/NavigationButtons";

import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";

import { useTranslations } from "next-intl";

import { StepProps } from "../types";

const PRESETS = [1, 2, 3, 4, 5, 6];

export default function DailyHoursStep({
  data,
  updateData,
  next,
  previous,
}: StepProps) {
  const t = useTranslations("onboarding.hours");

  return (
    <OnboardingCard
      title={t("title")}
      subtitle={t("subtitle")}
    >
      <div className="space-y-8">

        <div className="text-center">
          <h2 className="text-5xl font-bold text-brand-violet">
            {t("short", { count: data.daily_hours })}
          </h2>

          <p className="mt-2 text-muted-foreground">
            {t("everyDay")}
          </p>
        </div>

        <Slider
          value={[data.daily_hours]}
          min={1}
          max={8}
          step={1}
          onValueChange={(value) =>
            updateData({
              daily_hours: Array.isArray(value) ? value[0] : value,
            })
          }
        />

        <div className="flex flex-wrap justify-center gap-3">
          {PRESETS.map((hour) => (
            <Button
              key={hour}
              variant={
                data.daily_hours === hour
                  ? "default"
                  : "outline"
              }
              onClick={() =>
                updateData({
                  daily_hours: hour,
                })
              }
            >
              {t("preset", { count: hour })}
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