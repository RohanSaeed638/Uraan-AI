"use client";

import OnboardingCard from "@/components/onboarding/OnboardingCard";
import NavigationButtons from "@/components/onboarding/NavigationButtons";
import WelcomeBirdIllustration from "@/components/illustrations/WelcomeBirdIllustration";
import { useTranslations } from "next-intl";
import { StepProps } from "../types";
import { Rocket, Target, Calendar, Brain, LucideIcon } from "lucide-react";

const features: { icon: LucideIcon; key: "f1" | "f2" | "f3" | "f4" }[] = [
  { icon: Rocket, key: "f1" },
  { icon: Calendar, key: "f2" },
  { icon: Brain, key: "f3" },
  { icon: Target, key: "f4" },
];

export default function WelcomeStep({ next }: StepProps) {
  const t = useTranslations("onboarding.welcome");
  const tNav = useTranslations("onboarding.nav");

  return (
    <OnboardingCard
      title={t("title")}
      subtitle={t("subtitle")}
      illustration={<WelcomeBirdIllustration />}
    >
      <div className="grid gap-5 sm:grid-cols-2">
        {features.map(({ icon: Icon, key }) => (
          <div key={key} className="flex items-center gap-4">
            <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-brand-gold/15 text-brand-gold-deep dark:text-brand-gold">
              <Icon size={20} />
            </span>
            <div>
              <h3 className="font-semibold">{t(key)}</h3>
              <p className="text-sm text-muted-foreground">{t(`${key}t`)}</p>
            </div>
          </div>
        ))}
      </div>

      <NavigationButtons onNext={next} nextLabel={tNav("begin")} />
    </OnboardingCard>
  );
}
