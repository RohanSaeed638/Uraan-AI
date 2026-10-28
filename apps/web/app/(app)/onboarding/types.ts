export type SkillLevel =
  | "beginner"
  | "intermediate"
  | "advanced";

// Must match the backend enum values.
export type LearningStyle =
  | "reading"
  | "reading_video"
  | "reading_video_project";

export interface OnboardingForm {
  full_name: string;

  language: string;

  career_slug: string;

  skill_level: SkillLevel;

  learning_style: LearningStyle;

  daily_hours: number;

  target_duration: number;

  // Optional "About you" / "Your plan" answers (null = skipped).
  age: number | null;

  education: string | null;

  device: string | null;

  goal_type: string | null;

  preferred_study_hours: string | null;

  learning_pace: string | null;

  weekend_study: boolean | null;

  career_stage?: string;

  learning_goal?: string;

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