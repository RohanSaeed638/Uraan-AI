import { api } from "./client";

export const FEEDBACK_REASONS = ["wrong", "unclear", "too_hard", "too_easy", "broken_link", "other"] as const;

export type FeedbackReason = (typeof FEEDBACK_REASONS)[number];

export interface LessonFeedback {
  helpful: boolean;
  reason: FeedbackReason | null;
  comment: string | null;
}

/** The learner's own vote on a lesson, or null if they have not voted. */
export const getLessonFeedback = (unitId: string) =>
  api.get<LessonFeedback | null>(`/learning-units/${unitId}/feedback`).then((r) => r.data);

export const saveLessonFeedback = (
  unitId: string,
  body: { helpful: boolean; reason?: FeedbackReason | null; comment?: string | null }
) => api.put<LessonFeedback>(`/learning-units/${unitId}/feedback`, body).then((r) => r.data);

export const clearLessonFeedback = (unitId: string) => api.delete(`/learning-units/${unitId}/feedback`);
