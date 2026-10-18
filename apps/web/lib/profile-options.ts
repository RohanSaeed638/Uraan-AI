import { CAREERS, LANGUAGES } from "@/app/(app)/onboarding/constants";

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
  const detail = (error as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail) && detail[0]?.msg) {
    const field = Array.isArray(detail[0].loc)
      ? String(detail[0].loc[detail[0].loc.length - 1])
      : "";
    const msg = String(detail[0].msg).replace(/^Value error, /, "");

    return field ? `${titleCase(field)}: ${msg}` : msg;
  }

  return fallback;
}
