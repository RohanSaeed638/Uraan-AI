import { careers as fallbackCareers } from "@/lib/constants/careers";

export const TOTAL_STEPS = 12;

export const CAREERS = fallbackCareers.map(({ value, label }) => ({
  value,
  label,
}));

export const LANGUAGES = [
  {
    label: "English",
    value: "en",
  },
  {
    label: "اردو",
    value: "ur",
  },
  {
    label: "Roman Urdu",
    value: "ur-Latn",
  },
];

export const HOURS = [1,2,3,4,5,6];

export const DURATIONS = [3,6,9,12];
export const STEP_LABELS = [
  "Welcome",
  "Your name",
  "Language",
  "Career",
  "About you",
  "Skill level",
  "Learning style",
  "Daily hours",
  "Target duration",
  "Your plan",
  "Review",
  "Generating",
];

// Groups the 12 granular steps into the 4 visible stages shown in the
// stepper UI. Welcome (0) and Generating (11) are intro/outro splashes and
// don't belong to any stage — the page hides the indicator for those.
export const STAGES = [
  { label: "career" },
  { label: "skills" },
  { label: "style" },
  { label: "goals" },
];

// index = raw step (0-11), value = stage index (0-3), or null if the step
// has no stage (Welcome / Generating).
export const STEP_TO_STAGE: (number | null)[] = [
  null, // 0 Welcome
  0, // 1 Profile (name) -> Career
  0, // 2 Language -> Career
  0, // 3 Career -> Career
  1, // 4 About you -> Skills
  1, // 5 Skill level -> Skills
  2, // 6 Learning style -> Learning Style
  3, // 7 Daily hours -> Goals
  3, // 8 Target duration -> Goals
  3, // 9 Your plan -> Goals
  3, // 10 Review -> Goals
  null, // 11 Generating
];
