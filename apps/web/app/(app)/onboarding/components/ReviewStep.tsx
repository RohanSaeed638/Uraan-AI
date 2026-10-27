"use client";

import OnboardingCard from "@/components/onboarding/OnboardingCard";
import NavigationButtons from "@/components/onboarding/NavigationButtons";
import SummaryCard from "@/components/onboarding/SummaryCard";
import CheckIllustration from "@/components/illustrations/CheckIllustration";

import { useTranslations } from "next-intl";

import { LOCALE_LABELS, isLocale } from "@/i18n/config";
import { useCareerOptions } from "@/lib/careers";

import { StepProps } from "../types";

export default function ReviewStep({
  data,
  previous,
  next: submit,
}: StepProps) {
  const t = useTranslations("onboarding.review");
  const o = useTranslations("options");
  const { options: careers } = useCareerOptions();

  const choice = (group: string, value: string | null) =>
    value ? o(`${group}.${value}`) : null;

  const extras: [string, string | null][] = [
    [t("age"), data.age ? String(data.age) : null],
    [t("education"), choice("education", data.education)],
    [t("device"), choice("device", data.device)],
    [t("goal"), choice("goal_type", data.goal_type)],
    [t("hours"), choice("study_hours", data.preferred_study_hours)],
    [t("pace"), choice("pace", data.learning_pace)],
    [
      t("weekend"),
      data.weekend_study === null
        ? null
        : data.weekend_study
          ? t("yes")
          : t("no"),
    ],
  ];

  return (
    <OnboardingCard
      title={t("title")}
      subtitle={t("subtitle")}
      illustration={<CheckIllustration />}
    >
      <div className="grid grid-cols-2 gap-4">

        <SummaryCard
          label={t("name")}
          value={data.full_name}
        />

        <SummaryCard
          label={t("language")}
          value={LOCALE_LABELS[isLocale(data.language) ? data.language : "en"]}
        />

        <SummaryCard
          label={t("career")}
          value={careers.find((c) => c.value === data.career_slug)?.label ?? data.career_slug}
        />

        <SummaryCard
          label={t("skill")}
          value={o(`skill_level.${data.skill_level}`)}
        />

        <SummaryCard
          label={t("style")}
          value={o(`learning_style.${data.learning_style}`)}
        />

        <SummaryCard
          label={t("dailyHours")}
          value={t("hrs", { count: data.daily_hours })}
        />

        <SummaryCard
          label={t("target")}
          value={t("months", { count: data.target_duration })}
        />

        {extras
          .filter(([, value]) => value)
          .map(([label, value]) => (
            <SummaryCard key={label} label={label} value={value as string} />
          ))}

      </div>

      <NavigationButtons
        showBack
        onBack={previous}
        onNext={submit}
        nextLabel={t("generate")}
      />
    </OnboardingCard>
  );
}