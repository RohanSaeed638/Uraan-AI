export type SkillLevel =
  | "beginner"
  | "intermediate"
  | "advanced";

export type LearningStyle =
  | "videos"
  | "reading"
  | "projects"
  | "mixed";

export interface OnboardingForm {
  full_name: string;

  language: string;

  career_slug: string;

  skill_level: SkillLevel;

  learning_style: LearningStyle;

  daily_hours: number;

  target_duration: number;

  onboarding_completed: boolean;
}

export interface StepProps {
  data: OnboardingForm;

  updateData: (
    values: Partial<OnboardingForm>
  ) => void;

  next: () => void;

  previous: () => void;
}