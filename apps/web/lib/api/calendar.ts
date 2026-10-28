import { api } from "./client";
import { CalendarSchedule } from "@/types/api";

export const moveLesson = (unitId: string, date: string) =>
  api
    .put<CalendarSchedule>(`/calendar/units/${unitId}/date`, { date })
    .then((r) => r.data);

/** Lets the planner place the lesson again. */
export const unpinLesson = (unitId: string) =>
  api.delete<CalendarSchedule>(`/calendar/units/${unitId}/date`).then((r) => r.data);

/** Tells the planner about your time in plain words ("exams next week"). */
export const optimiseSchedule = (request: string) =>
  api.post<CalendarSchedule>("/calendar/optimise", { request }).then((r) => r.data);

export const resetSchedulePreferences = () =>
  api.delete<CalendarSchedule>("/calendar/preferences").then((r) => r.data);

export const getSchedule = () =>
  api.get<CalendarSchedule>("/calendar/schedule").then((r) => r.data);

export const regenerateCalendarLink = () =>
  api
    .post<{ token: string }>("/calendar/subscription/regenerate")
    .then((r) => r.data.token);
