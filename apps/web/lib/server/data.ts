import type { AchievementsResult } from "@/lib/api/achievements";
import { API_BASE } from "@/lib/api-base";
import { createClient } from "@/lib/supabase/server";
import type { AdminStats } from "@/lib/api/admin";
import { Roadmap, RoadmapSummary } from "@/types/roadmap";
import {
  CalendarSchedule,
  CareerDetail,
  CareerList,
  ProfileData,
  CareerDocument,
  DashboardSummary,
  Gamification,
  InterviewListItem,
  InterviewSession,
  Leaderboard,
  LeaderboardPeriod,
  Portfolio,
  ProgressOverview,
  ProjectList,
  UserSettings,
} from "@/types/api";

async function authedFetch(path: string) {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  return fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${session?.access_token}` },
    cache: "no-store",
  });
}

/** Every non-archived roadmap with phases, tasks and learning units. */
export async function getRoadmapDetails(): Promise<Roadmap[]> {
  try {
    const res = await authedFetch("/roadmaps");
    if (!res.ok) return [];

    const list = await res.json();
    if (!Array.isArray(list)) return [];

    const summaries = (list as RoadmapSummary[]).filter(
      (r) => r.status !== "archived"
    );

    const details = await Promise.all(
      summaries.map(async (summary) => {
        const detail = await authedFetch(`/roadmaps/${summary.id}`);
        return detail.ok ? ((await detail.json()) as Roadmap) : null;
      })
    );

    return details.filter((r): r is Roadmap => r !== null);
  } catch {
    return [];
  }
}

async function getJson<T>(path: string): Promise<T | null> {
  try {
    const res = await authedFetch(path);
    return res.ok ? ((await res.json()) as T) : null;
  } catch {
    return null;
  }
}

/** Signed in as an admin (the API answers 403 to everyone else). */
export async function getAdminMe(): Promise<
  { id: string; name: string; email: string | null } | "forbidden" | "error"
> {
  try {
    const res = await authedFetch("/admin/me");

    if (res.ok) return await res.json();

    // Only a clear "no" means not an admin; anything else is a problem to show, not a 404.
    return res.status === 401 || res.status === 403 ? "forbidden" : "error";
  } catch {
    return "error";
  }
}

export const getAdminStats = () => getJson<AdminStats>("/admin/stats");

export const getDashboardSummary = () =>
  getJson<DashboardSummary>("/dashboard/summary");

export const getGamification = () =>
  getJson<Gamification>("/gamification/me");

export const getInterviews = () =>
  getJson<{ sessions: InterviewListItem[] }>("/interviews");

export const getInterview = (id: string) =>
  getJson<InterviewSession>(`/interviews/${encodeURIComponent(id)}`);

export const getPortfolio = () => getJson<Portfolio>("/portfolio");

export const getDocuments = () =>
  getJson<{ documents: CareerDocument[] }>("/documents");

export const getCalendarSchedule = () =>
  getJson<CalendarSchedule>("/calendar/schedule");

export const getCalendarToken = () =>
  getJson<{ token: string }>("/calendar/subscription");

export const getLeaderboard = (period: LeaderboardPeriod) =>
  getJson<Leaderboard>(`/leaderboard?period=${period}`);

export const getProgressOverview = () =>
  getJson<ProgressOverview>("/progress/overview");

export const getAchievementsServer = () => getJson<AchievementsResult>("/achievements");

export const getActivity = () =>
  getJson<{ days: { date: string; count: number; xp: number }[] }>("/progress/activity?days=120");

export const getProjects = () => getJson<ProjectList>("/projects");

export const getUserSettings = () => getJson<UserSettings>("/settings");

export type Profile = ProfileData;

export async function getProfileServer(): Promise<Profile | null> {
  try {
    const res = await authedFetch("/profile/me");
    return res.ok ? ((await res.json()) as Profile) : null;
  } catch {
    return null;
  }
}

export const getCareersServer = () =>
  getJson<CareerList>("/careers?page_size=50");

export const getCareerDetailServer = (slug: string) =>
  getJson<CareerDetail>(`/careers/${encodeURIComponent(slug)}`);

export async function compareCareersServer(
  slugs: string[]
): Promise<CareerDetail[] | null> {
  try {
    const supabase = await createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();

    const res = await fetch(`${API_BASE}/careers/compare`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${session?.access_token}`,
      },
      body: JSON.stringify({ slugs }),
      cache: "no-store",
    });

    return res.ok ? (await res.json()).careers : null;
  } catch {
    return null;
  }
}
