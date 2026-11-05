"use client";

import { useState } from "react";

import StageIndicator from "@/components/onboarding/StageIndicator";

import WelcomeStep from "./components/WelcomeStep";
import ProfileStep from "./components/ProfileStep";
import LanguageStep from "./components/LanguageStep";
import CareerStep from "./components/CareerStep";
import AboutYouStep from "./components/AboutYouStep";
import SkillLevelStep from "./components/SkillLevelStep";
import LearningStyleStep from "./components/LearningStyleStep";
import DailyHoursStep from "./components/DailyHoursStep";
import TargetDurationStep from "./components/TargetDurationStep";
import YourPlanStep from "./components/YourPlanStep";
import ReviewStep from "./components/ReviewStep";
import GeneratingStep from "./components/GeneratingStep";
import { useMutation } from "@tanstack/react-query";
import { updateProfile } from "@/lib/api/profile";

import { toast } from "sonner";

import { apiErrorMessage } from "@/lib/profile-options";

import { STAGES, STEP_TO_STAGE } from "./constants";

const REVIEW_STEP = 10;

import { OnboardingForm } from "./types";
import {
  finishRoadmap,
  generateRoadmap,
  RoadmapJobError,
} from "@/services/roadmap";
import {useRouter} from "next/navigation";
import { useTranslations } from "next-intl";

const STAGE_FOR_SKILL = {
  beginner: "beginner",
  intermediate: "student",
  advanced: "job_ready",
} as const;

/** "backend-engineer" -> "Backend Engineer". */
const prettyCareer = (slug: string) =>
  slug.replace(/[-_]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

const initialData: OnboardingForm = {

  full_name: "",

  language: "en",

  career_slug: "",

  skill_level: "beginner",

  learning_style: "reading",

  daily_hours: 2,

  target_duration: 12,

  age: null,

  education: null,

  device: null,

  goal_type: null,

  preferred_study_hours: null,

  learning_pace: null,

  weekend_study: null,

  onboarding_completed: false,

};

export default function OnboardingPage() {

  const [step, setStep] = useState(0);

  const [data, setData] =
    useState(initialData);

  const router = useRouter();
  const t = useTranslations("onboarding");
  const updateProfileMutation = useMutation({
    mutationFn: updateProfile,
  });

  const generateRoadmapMutation = useMutation({
    mutationFn: generateRoadmap,
});

  const updateData = (
    values: Partial<OnboardingForm>
  ) => {

    setData((prev) => ({
      ...prev,
      ...values,
    }));

  };


  const next = () =>
    setStep((s) => s + 1);

  const previous = () =>
    setStep((s) => s - 1);

  const onSubmit = async () => {
    try {
        next();
        // The roadmap request needs a stage and a goal that the steps do not
        // ask for, so derive them from the skill level and the career.
        const career_stage = STAGE_FOR_SKILL[data.skill_level];
        const learning_goal = `Become a job-ready ${prettyCareer(data.career_slug)}`;

        await updateProfileMutation.mutateAsync({
          ...data,
          career_stage,
          learning_goal,
          onboarding_completed: true,
        });

        const started = await generateRoadmapMutation.mutateAsync({
          career_slug: data.career_slug,
          career_stage,
          skill_level: data.skill_level,
          learning_goal,
          daily_hours: data.daily_hours,
          target_duration: data.target_duration,
          learning_style: data.learning_style,
        });

        // The roadmap is built in the background: wait for it to be ready.
        await finishRoadmap(started.data.id);

        router.push(`/roadmaps/${started.data.id}`);


    } catch (error) {

        console.error(error);

        // Back to the review step with the answers intact, not a dead
        // "Generating" screen.
        setStep(REVIEW_STEP);
        toast.error(
          error instanceof RoadmapJobError
            ? error.message
            : apiErrorMessage(error, t("failed"))
        );

    }
  };

  const steps = [

    <WelcomeStep
      key={0}
      data={data}
      updateData={updateData}
      next={next}
      previous={previous}
    />,

    <ProfileStep
      key={1}
      data={data}
      updateData={updateData}
      next={next}
      previous={previous}
    />,

    <LanguageStep
      key={2}
      data={data}
      updateData={updateData}
      next={next}
      previous={previous}
    />,

    <CareerStep
      key={3}
      data={data}
      updateData={updateData}
      next={next}
      previous={previous}
    />,

    <AboutYouStep
      key={4}
      data={data}
      updateData={updateData}
      next={next}
      previous={previous}
    />,

    <SkillLevelStep
      key={5}
      data={data}
      updateData={updateData}
      next={next}
      previous={previous}
    />,

    <LearningStyleStep
      key={6}
      data={data}
      updateData={updateData}
      next={next}
      previous={previous}
    />,

    <DailyHoursStep
      key={7}
      data={data}
      updateData={updateData}
      next={next}
      previous={previous}
    />,

    <TargetDurationStep
      key={8}
      data={data}
      updateData={updateData}
      next={next}
      previous={previous}
    />,

    <YourPlanStep
      key={9}
      data={data}
      updateData={updateData}
      next={next}
      previous={previous}
    />,

    <ReviewStep
      key={10}
      data={data}
      updateData={updateData}
      next={onSubmit}
      previous={previous}
    />,

    <GeneratingStep
      key={11}
    />,

  ];

  const activeStage = STEP_TO_STAGE[step];

  return (
    <div className="mx-auto max-w-5xl p-8">
      {activeStage !== null && (
        <StageIndicator stages={STAGES} activeStage={activeStage} />
      )}

      {steps[step]}
    </div>
  );
}