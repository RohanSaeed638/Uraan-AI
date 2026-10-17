export const TOTAL_STEPS = 10;

export const CAREERS = [
  {
    label: "Backend Engineer",
    value: "backend-engineer",
  },
  {
    label: "Frontend Engineer",
    value: "frontend-engineer",
  },
  {
    label: "Full Stack Engineer",
    value: "fullstack-engineer",
  },
  {
    label: "AI Engineer",
    value: "ai-engineer",
  },
  {
    label: "Data Scientist",
    value: "data-scientist",
  },
  {
    label: "Cyber Security",
    value: "cyber-security",
  },
  {
    label: "Cloud Engineer",
    value: "cloud-engineer",
  },
  {
    label: "DevOps Engineer",
    value: "devops-engineer",
  },
];

export const LANGUAGES = [
  {
    label: "English",
    value: "en",
  },
  {
    label: "اردو",
    value: "ur",
  },
];

export const HOURS = [1,2,3,4,5,6];

export const DURATIONS = [3,6,9,12];
export const STEP_LABELS = [
  "Welcome",
  "Your name",
  "Language",
  "Career",
  "Skill level",
  "Learning style",
  "Daily hours",
  "Target duration",
  "Review",
  "Generating",
];

// Groups the 10 granular steps into the 4 visible stages shown in the
// stepper UI. Welcome (0) and Generating (9) are intro/outro splashes and
// don't belong to any stage — the page hides the indicator for those.
export const STAGES = [
  { label: "Career" },
  { label: "Skills" },
  { label: "Learning Style" },
  { label: "Goals" },
];

// index = raw step (0-9), value = stage index (0-3), or null if the step
// has no stage (Welcome / Generating).
export const STEP_TO_STAGE: (number | null)[] = [
  null, // 0 Welcome
  0, // 1 Profile (name) -> Career
  0, // 2 Language -> Career
  0, // 3 Career -> Career
  1, // 4 Skill level -> Skills
  2, // 5 Learning style -> Learning Style
  3, // 6 Daily hours -> Goals
  3, // 7 Target duration -> Goals
  3, // 8 Review -> Goals
  null, // 9 Generating
];
