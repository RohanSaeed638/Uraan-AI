"use client";

import { useState } from "react";

import StepIndicator from "@/components/onboarding/StepIndicator";

import WelcomeStep from "./components/WelcomeStep";
import ProfileStep from "./components/ProfileStep";
import LanguageStep from "./components/LanguageStep";
import CareerStep from "./components/CareerStep";
import SkillLevelStep from "./components/SkillLevelStep";
import LearningStyleStep from "./components/LearningStyleStep";
import DailyHoursStep from "./components/DailyHoursStep";
import TargetDurationStep from "./components/TargetDurationStep";
import ReviewStep from "./components/ReviewStep";
import GeneratingStep from "./components/GeneratingStep";
import { useMutation } from "@tanstack/react-query";
import { updateProfile } from "@/lib/api/profile";

import { TOTAL_STEPS } from "./constants";

import { OnboardingForm } from "./types";
import { generateRoadmap } from "@/services/roadmap";
import {useRouter} from "next/navigation";

const initialData: OnboardingForm = {

  full_name: "",

  language: "en",

  career_slug: "",

  skill_level: "beginner",

  learning_style: "mixed",

  daily_hours: 2,

  target_duration: 12,

  onboarding_completed: false,

};

export default function OnboardingPage() {

  const [step, setStep] = useState(0);

  const [data, setData] =
    useState(initialData);

  const router = useRouter();
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
        await updateProfileMutation.mutateAsync(data);

        const roadmap =
        await generateRoadmapMutation.mutateAsync();

        router.push(`/roadmap/${roadmap.data.id}`);


    } catch (error) {

        console.error(error);

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

    <SkillLevelStep
      key={4}
      data={data}
      updateData={updateData}
      next={next}
      previous={previous}
    />,

    <LearningStyleStep
      key={5}
      data={data}
      updateData={updateData}
      next={next}
      previous={previous}
    />,

    <DailyHoursStep
      key={6}
      data={data}
      updateData={updateData}
      next={next}
      previous={previous}
    />,

    <TargetDurationStep
      key={7}
      data={data}
      updateData={updateData}
      next={next}
      previous={previous}
    />,

    <ReviewStep
      key={8}
      data={data}
      updateData={updateData}
      next={onSubmit}
      previous={previous}
    />,

    <GeneratingStep
      key={9}
    />,

  ];

  return (

    <main className="mx-auto max-w-5xl p-8">

      <StepIndicator
        current={step}
        total={TOTAL_STEPS}
      />

      {steps[step]}

    </main>

  );

}