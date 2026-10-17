"use client";

import OnboardingCard from "@/components/onboarding/OnboardingCard";
import NavigationButtons from "@/components/onboarding/NavigationButtons";
import WelcomeBirdIllustration from "@/components/illustrations/WelcomeBirdIllustration";
import { StepProps } from "../types";
import { Rocket, Target, Calendar, Brain, LucideIcon } from "lucide-react";

const features: { icon: LucideIcon; title: string; description: string }[] = [
  {
    icon: Rocket,
    title: "Personalized Roadmap",
    description: "Tailored for your goals.",
  },
  {
    icon: Calendar,
    title: "Daily Schedule",
    description: "Learn consistently every day.",
  },
  {
    icon: Brain,
    title: "AI Powered",
    description: "Dynamic learning path.",
  },
  {
    icon: Target,
    title: "Job Ready",
    description: "Real projects and interview prep.",
  },
];

export default function WelcomeStep({ next }: StepProps) {
  return (
    <OnboardingCard
      title="Welcome to Uraan AI 🚀"
      subtitle="Let's create your personalized career roadmap."
      illustration={<WelcomeBirdIllustration />}
    >
      <div className="grid gap-5 sm:grid-cols-2">
        {features.map(({ icon: Icon, title, description }) => (
          <div key={title} className="flex items-center gap-4">
            <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-brand-violet/10 text-brand-violet">
              <Icon size={20} />
            </span>
            <div>
              <h3 className="font-semibold">{title}</h3>
              <p className="text-sm text-muted-foreground">{description}</p>
            </div>
          </div>
        ))}
      </div>

      <NavigationButtons onNext={next} nextLabel="Let's Begin" />
    </OnboardingCard>
  );
}
