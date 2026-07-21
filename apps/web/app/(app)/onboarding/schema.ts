import { z } from "zod";

export const onboardingSchema = z.object({

  full_name: z.string().min(2),

  language: z.string(),

  career_slug: z.string(),

  skill_level: z.enum([
    "beginner",
    "intermediate",
    "advanced",
  ]),

  learning_style: z.enum([
    "videos",
    "reading",
    "projects",
    "mixed",
  ]),

  daily_hours: z
    .number()
    .min(1)
    .max(12),

  target_duration: z.number(),

  onboarding_completed:
    z.boolean(),

});

export type OnboardingSchema =
  z.infer<typeof onboardingSchema>;