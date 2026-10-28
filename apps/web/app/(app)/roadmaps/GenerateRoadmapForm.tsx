"use client";

import { useForm } from "react-hook-form";
import { useTranslations } from "next-intl";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { Textarea } from "@/components/ui/textarea";
import NativeSelect from "@/components/shared/NativeSelect";
import { Input } from "@/components/ui/input";
import { useCareerOptions } from "@/lib/careers";
import { Button } from "@/components/ui/button";

import {
  CareerStage,
  LearningStyle,
  SkillLevel,
  GenerateRoadmapFormValues,
} from "@/types/roadmap";

interface GenerateRoadmapFormProps {
  loading?: boolean;
  onSubmit: (values: GenerateRoadmapFormValues) => void;
  defaultCareer?: string;
}

export default function GenerateRoadmapForm({
  loading = false,
  onSubmit,
  defaultCareer = "",
}: GenerateRoadmapFormProps) {
  const t = useTranslations("roadmapForm");
  const tStage = useTranslations("options.career_stage");
  const tSkill = useTranslations("options.skill_level");
  const tStyle = useTranslations("options.learning_style");
  const { options: careerOptions } = useCareerOptions();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<GenerateRoadmapFormValues>({
    defaultValues: {
      career_slug: defaultCareer,
      career_stage: undefined,
      skill_level: undefined,
      learning_goal: "",
      daily_hours: 2,
      target_duration: 6,
      learning_style: undefined,
    },
  });

  const careerStage = watch("career_stage");
  const skillLevel = watch("skill_level");
  const learningStyle = watch("learning_style");

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="space-y-6"
    >
      {/* Career */}
      <div className="space-y-2">
        <label
          htmlFor="career_slug"
          className="text-sm font-medium"
        >
          {t("career")}
        </label>

        <NativeSelect
          id="career_slug"
          {...register("career_slug", {
            required: t("careerRequired"),
          })}
        >
          <option value="">{t("careerPlaceholder")}</option>
          {careerOptions.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </NativeSelect>

        {errors.career_slug && (
          <p className="text-sm text-destructive">
            {errors.career_slug.message}
          </p>
        )}
      </div>

      {/* Career Stage */}
      <div className="space-y-2">
        <label className="text-sm font-medium">
          {t("stage")}
        </label>

        <Select
          value={careerStage}
          onValueChange={(value) =>
            setValue(
              "career_stage",
              value as CareerStage,
              {
                shouldValidate: true,
              }
            )
          }
        >
          <SelectTrigger>
            <SelectValue placeholder={t("stagePlaceholder")} />
          </SelectTrigger>

          <SelectContent>
            <SelectItem value={CareerStage.BEGINNER}>
              {tStage("beginner")}
            </SelectItem>

            <SelectItem value={CareerStage.STUDENT}>
              {tStage("student")}
            </SelectItem>

            <SelectItem value={CareerStage.JOB_READY}>
              {tStage("job_ready")}
            </SelectItem>

            <SelectItem value={CareerStage.PROFESSIONAL}>
              {tStage("professional")}
            </SelectItem>

            <SelectItem value={CareerStage.CAREER_SWITCHER}>
              {tStage("career_switcher")}
            </SelectItem>
          </SelectContent>
        </Select>

        {errors.career_stage && (
          <p className="text-sm text-destructive">
            {t("stageRequired")}
          </p>
        )}
      </div>

      {/* Skill Level */}
      <div className="space-y-2">
        <label className="text-sm font-medium">
          {t("skill")}
        </label>

        <Select
          value={skillLevel}
          onValueChange={(value) =>
            setValue(
              "skill_level",
              value as SkillLevel,
              {
                shouldValidate: true,
              }
            )
          }
        >
          <SelectTrigger>
            <SelectValue placeholder={t("skillPlaceholder")} />
          </SelectTrigger>

          <SelectContent>
            <SelectItem value={SkillLevel.BEGINNER}>
              {tSkill("beginner")}
            </SelectItem>

            <SelectItem value={SkillLevel.INTERMEDIATE}>
              {tSkill("intermediate")}
            </SelectItem>

            <SelectItem value={SkillLevel.ADVANCED}>
              {tSkill("advanced")}
            </SelectItem>
          </SelectContent>
        </Select>

        {errors.skill_level && (
          <p className="text-sm text-destructive">
            {t("skillRequired")}
          </p>
        )}
      </div>

      {/* Learning Goal */}
      <div className="space-y-2">
        <label
          htmlFor="learning_goal"
          className="text-sm font-medium"
        >
          {t("goal")}
        </label>

        <Textarea
          id="learning_goal"
          rows={5}
          placeholder={t("goalPlaceholder")}
          {...register("learning_goal", {
            required: t("goalRequired"),
            minLength: {
              value: 10,
              message: t("goalShort"),
            },
          })}
        />

        {errors.learning_goal && (
          <p className="text-sm text-destructive">
            {errors.learning_goal.message}
          </p>
        )}
      </div>

      {/* Daily Hours */}
      <div className="space-y-2">
        <label
          htmlFor="daily_hours"
          className="text-sm font-medium"
        >
          {t("hours")}
        </label>

        <Input
          id="daily_hours"
          type="number"
          min={1}
          max={12}
          {...register("daily_hours", {
            required: t("hoursRequired"),
            valueAsNumber: true,
            min: {
              value: 1,
              message: t("hoursMin"),
            },
            max: {
              value: 12,
              message: t("hoursMax"),
            },
          })}
        />

        {errors.daily_hours && (
          <p className="text-sm text-destructive">
            {errors.daily_hours.message}
          </p>
        )}
      </div>

      {/* Target Duration */}
      <div className="space-y-2">
        <label
          htmlFor="target_duration"
          className="text-sm font-medium"
        >
          {t("months")}
        </label>

        <Input
          id="target_duration"
          type="number"
          min={1}
          max={36}
          {...register("target_duration", {
            required: t("monthsRequired"),
            valueAsNumber: true,
            min: {
              value: 1,
              message: t("monthsMin"),
            },
            max: {
              value: 36,
              message: t("monthsMax"),
            },
          })}
        />

        {errors.target_duration && (
          <p className="text-sm text-destructive">
            {errors.target_duration.message}
          </p>
        )}
      </div>

      {/* Learning Style */}
      <div className="space-y-2">
        <label className="text-sm font-medium">
          {t("style")}
        </label>

        <Select
          value={learningStyle}
          onValueChange={(value) =>
            setValue(
              "learning_style",
              value as LearningStyle,
              {
                shouldValidate: true,
              }
            )
          }
        >
          <SelectTrigger>
            <SelectValue placeholder={t("stylePlaceholder")} />
          </SelectTrigger>

          <SelectContent>
            <SelectItem value={LearningStyle.READING}>
              {tStyle("reading")}
            </SelectItem>
            <SelectItem value={LearningStyle.READING_VIDEO}>
              {tStyle("reading_video")}
            </SelectItem>
            <SelectItem value={LearningStyle.READING_VIDEO_PROJECT}>
              {tStyle("reading_video_project")}
            </SelectItem>
          </SelectContent>
        </Select>

        {errors.learning_style && (
          <p className="text-sm text-destructive">
            {t("styleRequired")}
          </p>
        )}
      </div>

      {/* Submit */}
      <Button
        type="submit"
        className="w-full"
        disabled={loading}
      >
        {loading ? t("submitting") : t("submit")}
      </Button>
    </form>
  );
}