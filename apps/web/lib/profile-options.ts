import { CAREERS, LANGUAGES } from "@/app/(app)/onboarding/constants";
import { translateApiMessage } from "@/lib/api-errors";

export { CAREERS, LANGUAGES };

export const SKILL_LEVELS = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
] as const;

export const LEARNING_STYLES = [
  { value: "reading", label: "Reading" },
  { value: "reading_video", label: "Reading + Videos" },
  { value: "reading_video_project", label: "Reading + Videos + Projects" },
] as const;

export const CAREER_STAGES = [
  { value: "student", label: "Student" },
  { value: "beginner", label: "Beginner" },
  { value: "job_ready", label: "Job ready" },
  { value: "professional", label: "Working professional" },
  { value: "career_switcher", label: "Career switcher" },
] as const;

// Value lists for the onboarding "About you" / "Your plan" answers. Labels
// live in messages/*.json under `options.<name>.<value>`.
export const EDUCATION = [
  "school",
  "college",
  "bachelors",
  "masters",
  "self_taught",
  "other",
] as const;

export const DEVICES = ["laptop", "desktop", "mobile"] as const;

export const GOAL_TYPES = [
  "local_job",
  "remote_job",
  "freelancing",
  "startup",
  "study_abroad",
] as const;

export const STUDY_HOURS = [
  "morning",
  "afternoon",
  "evening",
  "night",
  "flexible",
] as const;

export const PACES = ["relaxed", "steady", "intensive"] as const;

const COMMON_TIMEZONES = [
  "UTC",
  "Asia/Karachi",
  "Asia/Dubai",
  "Asia/Kolkata",
  "Asia/Dhaka",
  "Europe/London",
  "Europe/Istanbul",
  "America/New_York",
  "America/Los_Angeles",
];

/** Every IANA timezone the browser knows, or a short list as a fallback. */
export function listTimezones(): string[] {
  try {
    return Intl.supportedValuesOf("timeZone");
  } catch {
    return COMMON_TIMEZONES;
  }
}

export function deviceTimezone(): string | null {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || null;
  } catch {
    return null;
  }
}

/** "backend-engineer" -> "Backend Engineer", "job_ready" -> "Job Ready". */
export function titleCase(value?: string | null): string {
  if (!value) return "Not set";

  return value.replace(/[-_]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function labelFor(
  options: readonly { value: string; label: string }[],
  value?: string | null
): string {
  if (!value) return "Not set";

  return options.find((o) => o.value === value)?.label ?? titleCase(value);
}

/** The first readable message from an API error response. */
export function apiErrorMessage(error: unknown, fallback: string): string {
  const data = (
    error as { response?: { data?: { detail?: unknown; message?: unknown } } }
  )?.response?.data;
  const detail = data?.detail;

  if (typeof detail === "string") return translateApiMessage(detail);

  // Unexpected server errors use a safe, readable `message` instead.
  if (typeof data?.message === "string") return translateApiMessage(data.message);

  if (Array.isArray(detail) && detail[0]?.msg) {
    const field = Array.isArray(detail[0].loc)
      ? String(detail[0].loc[detail[0].loc.length - 1])
      : "";
    const msg = String(detail[0].msg).replace(/^Value error, /, "");

    return field ? `${titleCase(field)}: ${msg}` : msg;
  }

  return fallback;
}
