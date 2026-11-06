import { api } from "./client";

export interface FunnelStep {
  key: "signups" | "onboarded" | "roadmap" | "first_lesson" | "returned" | "finished";
  count: number;
  of_signups: number | null;
  of_previous: number | null;
}

export interface Cohort {
  week: string;
  signups: number;
  onboarded: number;
  roadmap: number;
  first_lesson: number;
  returned: number;
  finished: number;
  eligible_for_return: number;
}

export interface Funnel {
  weeks: number;
  eligible_for_return: number;
  steps: FunnelStep[];
  cohorts: Cohort[];
}

export interface FeedbackOverview {
  days: number;
  total: number;
  helpful: number;
  not_helpful: number;
  helpful_percent: number | null;
  by_reason: { reason: string; count: number }[];
  by_career: { career_slug: string; helpful: number; not_helpful: number; helpful_percent: number | null }[];
  topics: { task_title: string; career_slug: string | null; helpful: number; not_helpful: number }[];
  recent: {
    created_at: string;
    career_slug: string | null;
    task_title: string | null;
    lesson_title: string | null;
    lesson_type: string | null;
    reason: string | null;
    comment: string | null;
  }[];
}

export interface AiUsage {
  days: number;
  requests: number;
  failed: number;
  input_tokens: number;
  output_tokens: number;
  estimated_cost_usd: number | null;
  unpriced_tokens: number;
  daily_limit_per_user: number | null;
  users_over_limit_today: number | null;
  by_model: {
    provider: string;
    model: string;
    requests: number;
    failed: number;
    input_tokens: number;
    output_tokens: number;
    estimated_cost_usd: number | null;
  }[];
  by_purpose: { purpose: string; requests: number; failed: number; tokens: number }[];
  daily: { date: string; requests: number; tokens: number; estimated_cost_usd: number }[];
  top_users: { profile_id: string; name: string; requests: number; tokens: number }[];
}

export interface LinkOverview {
  ok: number;
  dead: number;
  unknown: number;
  last_checked: string | null;
  dead_links: { url: string; http_status: number | null; reason: string | null; fail_count: number; checked_at: string }[];
}

export const getFunnel = (weeks: number) =>
  api.get<Funnel>("/admin/insights/funnel", { params: { weeks } }).then((r) => r.data);

export const getFeedbackOverview = (days: number) =>
  api.get<FeedbackOverview>("/admin/insights/feedback", { params: { days } }).then((r) => r.data);

export const getAiUsage = (days: number) =>
  api.get<AiUsage>("/admin/insights/ai-usage", { params: { days } }).then((r) => r.data);

export const getLinkOverview = () =>
  api.get<LinkOverview>("/admin/insights/links").then((r) => r.data);
