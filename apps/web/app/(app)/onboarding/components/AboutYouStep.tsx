"use client";

import { useTranslations } from "next-intl";

import OnboardingCard from "@/components/onboarding/OnboardingCard";
import NavigationButtons from "@/components/onboarding/NavigationButtons";
import OptionCard from "@/components/onboarding/OptionCard";
import { Input } from "@/components/ui/input";

import { DEVICES, EDUCATION } from "@/lib/profile-options";

import { StepProps } from "../types";

export default function AboutYouStep({
  data,
  updateData,
  next,
  previous,
}: StepProps) {
  const t = useTranslations("onboarding.about");
  const o = useTranslations("options");

  const ageInvalid =
    data.age !== null && (data.age < 10 || data.age > 100);

  return (
    <OnboardingCard title={t("title")} subtitle={t("subtitle")}>
      <div className="space-y-8">
        <div className="space-y-2">
          <label htmlFor="age" className="block text-sm font-medium">
            {t("age")}
          </label>

          <Input
            id="age"
            type="number"
            inputMode="numeric"
            min={10}
            max={100}
            className="max-w-40"
            value={data.age ?? ""}
            onChange={(e) =>
              updateData({
                age: e.target.value === "" ? null : Number(e.target.value),
              })
            }
            aria-invalid={ageInvalid}
          />

          {ageInvalid && (
            <p className="text-sm text-destructive">{t("ageInvalid")}</p>
          )}
        </div>

        <div className="space-y-3">
          <p className="text-sm font-medium">{t("education")}</p>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {EDUCATION.map((value) => (
              <OptionCard
                key={value}
                title={o(`education.${value}`)}
                selected={data.education === value}
                onClick={() => updateData({ education: value })}
              />
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <p className="text-sm font-medium">{t("device")}</p>

          <div className="grid gap-3 sm:grid-cols-3">
            {DEVICES.map((value) => (
              <OptionCard
                key={value}
                title={o(`device.${value}`)}
                description={
                  value === "mobile" ? t("mobileHint") : undefined
                }
                selected={data.device === value}
                onClick={() => updateData({ device: value })}
              />
            ))}
          </div>
        </div>
      </div>

      <NavigationButtons
        showBack
        onBack={previous}
        onNext={ageInvalid ? () => {} : next}
        nextLabel={t("continue")}
      />
    </OnboardingCard>
  );
}
