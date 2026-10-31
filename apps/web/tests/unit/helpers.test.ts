import { afterEach, describe, expect, it } from "vitest";

import { authErrorKey } from "@/lib/auth-errors";
import { errorCode, setErrorLookup, translateApiMessage } from "@/lib/api-errors";
import { catalogKey } from "@/lib/career-text";
import { salaryRange } from "@/lib/careers";
import {
  addDays,
  dateKey,
  dayStatus,
  formatTime,
  monthName,
  parseDate,
  startOfWeek,
  weekdayIndex,
  weekdayNames,
} from "@/lib/planner";
import { apiErrorMessage, labelFor, titleCase } from "@/lib/profile-options";
import type { CalendarSchedule } from "@/types/api";

afterEach(() => setErrorLookup(null));

describe("error codes (must match the API's rule in app/core/error_codes.py)", () => {
  it.each([
    ["Profile not found", "profile_not_found"],
    ["  Too many requests -- try again!  ", "too_many_requests_try_again"],
    ["Roadmap #12 isn't yours", "roadmap_12_isn_t_yours"],
    ["", ""],
  ])("%s -> %s", (message, code) => {
    expect(errorCode(message)).toBe(code);
  });

  it("cuts long messages at 80 characters without leaving a trailing underscore", () => {
    const code = errorCode("word ".repeat(40));

    expect(code.length).toBeLessThanOrEqual(80);
    expect(code.endsWith("_")).toBe(false);
  });

  it("shows the translation when there is one and the English text otherwise", () => {
    expect(translateApiMessage("Profile not found")).toBe("Profile not found");

    setErrorLookup((code) => (code === "profile_not_found" ? "پروفائل نہیں ملی" : null));

    expect(translateApiMessage("Profile not found")).toBe("پروفائل نہیں ملی");
    expect(translateApiMessage("Something unlisted")).toBe("Something unlisted");
  });
});

describe("sign-in errors", () => {
  it.each([
    ["Invalid login credentials", "invalidCredentials"],
    ["Email not confirmed", "emailNotConfirmed"],
    ["User already registered", "alreadyRegistered"],
    ["A user has already been registered with this email", "alreadyRegistered"],
    ["email rate limit exceeded", "rateLimited"],
    ["Too many requests", "rateLimited"],
  ])("%s -> %s", (message, key) => {
    expect(authErrorKey(message)).toBe(key);
  });

  it("leaves unknown messages alone", () => {
    expect(authErrorKey("Database exploded")).toBeNull();
  });
});

describe("apiErrorMessage", () => {
  const failure = (data: unknown) => ({ response: { data } });

  it("prefers the API's text", () => {
    expect(apiErrorMessage(failure({ detail: "Profile not found" }), "fallback")).toBe("Profile not found");
  });

  it("falls back to the readable message of unexpected errors", () => {
    expect(apiErrorMessage(failure({ message: "Something went wrong on our side." }), "fallback")).toBe(
      "Something went wrong on our side."
    );
  });

  it("names the field in a validation error", () => {
    const error = failure({ detail: [{ loc: ["body", "daily_hours"], msg: "Value error, must be positive" }] });

    expect(apiErrorMessage(error, "fallback")).toBe("Daily Hours: must be positive");
  });

  it("uses the fallback when there is nothing readable", () => {
    expect(apiErrorMessage(new Error("network"), "fallback")).toBe("fallback");
    expect(apiErrorMessage(undefined, "fallback")).toBe("fallback");
  });
});

describe("labels", () => {
  it("makes readable titles from stored values", () => {
    expect(titleCase("backend-engineer")).toBe("Backend Engineer");
    expect(titleCase("job_ready")).toBe("Job Ready");
    expect(titleCase(null)).toBe("Not set");
  });

  it("uses the option's own label when it has one", () => {
    const options = [{ value: "mobile", label: "Phone only" }];

    expect(labelFor(options, "mobile")).toBe("Phone only");
    expect(labelFor(options, "laptop")).toBe("Laptop");
    expect(labelFor(options, undefined)).toBe("Not set");
  });
});

describe("careers", () => {
  it("writes salary ranges in thousands, and nothing when unknown", () => {
    expect(salaryRange(80000, 450000)).toBe("PKR 80k - 450k");
    expect(salaryRange(null, 450000)).toBeNull();
    expect(salaryRange(undefined, undefined)).toBeNull();
  });

  it("builds catalogue keys with the same rule as the sync script", () => {
    expect(catalogKey("Git and GitHub")).toBe("git_and_github");
    expect(catalogKey("C++ / C#")).toBe("c_c");
  });
});

describe("planner dates", () => {
  it("keeps a date as written, with no timezone shift", () => {
    expect(dateKey(parseDate("2026-11-03"))).toBe("2026-11-03");
    expect(dateKey(addDays(parseDate("2026-12-31"), 1))).toBe("2027-01-01");
  });

  it("starts weeks on Monday", () => {
    // Sunday 8 November 2026
    expect(dateKey(startOfWeek(parseDate("2026-11-08")))).toBe("2026-11-02");
    expect(dateKey(startOfWeek(parseDate("2026-11-02")))).toBe("2026-11-02");
    expect(weekdayIndex(parseDate("2026-11-02"))).toBe(0);
    expect(weekdayIndex(parseDate("2026-11-08"))).toBe(6);
  });

  it("names weekdays and months from the language", () => {
    expect(weekdayNames("en")).toHaveLength(7);
    expect(weekdayNames("en")[0]).toBe("Mon");
    expect(weekdayNames("en", "long")[6]).toBe("Sunday");
    expect(monthName(0, "en")).toBe("January");
  });

  it("shows times on a 12-hour clock", () => {
    expect(formatTime("19:00:00", "en")).toBe("7:00 PM");
    expect(formatTime("09:30:00", "en")).toBe("9:30 AM");
  });
});

describe("why a day is empty", () => {
  const schedule = {
    availability: { blocked_dates: ["2026-11-04"], weekday_minutes: [60, 60, 60, 60, 60, 0, 0] },
  } as unknown as CalendarSchedule;

  it("says planned when there is something on it", () => {
    expect(dayStatus(parseDate("2026-11-03"), schedule, {} as never)).toBe("planned");
  });

  it("says blocked for a day the learner blocked", () => {
    expect(dayStatus(parseDate("2026-11-04"), schedule, undefined)).toBe("blocked");
  });

  it("says rest for a day with no study time, and free otherwise", () => {
    expect(dayStatus(parseDate("2026-11-07"), schedule, undefined)).toBe("rest"); // Saturday
    expect(dayStatus(parseDate("2026-11-05"), schedule, undefined)).toBe("free");
  });
});
