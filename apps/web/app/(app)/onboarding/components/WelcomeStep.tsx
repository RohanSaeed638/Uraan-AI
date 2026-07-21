"use client";

import OnboardingCard from "@/components/onboarding/OnboardingCard";
import NavigationButtons from "@/components/onboarding/NavigationButtons";
import { StepProps } from "../types";
import { Rocket, Target, Calendar, Brain } from "lucide-react";

export default function WelcomeStep({
  next,
}: StepProps) {
  return (
    <OnboardingCard
      title="Welcome to Uraan AI 🚀"
      subtitle="Let's create your personalized career roadmap."
    >
      <div className="grid gap-6">

        <div className="flex items-center gap-4">
          <Rocket className="text-purple-600" />
          <div>
            <h3 className="font-semibold">
              Personalized Roadmap
            </h3>
            <p className="text-sm text-muted-foreground">
              Tailored for your goals.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Calendar className="text-purple-600" />
          <div>
            <h3 className="font-semibold">
              Daily Schedule
            </h3>
            <p className="text-sm text-muted-foreground">
              Learn consistently every day.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Brain className="text-purple-600" />
          <div>
            <h3 className="font-semibold">
              AI Powered
            </h3>
            <p className="text-sm text-muted-foreground">
              Dynamic learning path.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Target className="text-purple-600" />
          <div>
            <h3 className="font-semibold">
              Job Ready
            </h3>
            <p className="text-sm text-muted-foreground">
              Real projects and interview prep.
            </p>
          </div>
        </div>

      </div>

      <NavigationButtons
        onNext={next}
        nextLabel="Let's Begin"
      />
    </OnboardingCard>
  );
}