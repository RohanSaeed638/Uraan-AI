import { createClient } from "@/lib/supabase/server";
import { Roadmap, RoadmapSummary } from "@/types/roadmap";
import {
  DashboardSummary,
  ProgressOverview,
  ProjectList,
  UserSettings,
} from "@/types/api";

async function authedFetch(path: string) {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  return fetch(`${process.env.NEXT_PUBLIC_API_URL}${path}`, {
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

export const getDashboardSummary = () =>
  getJson<DashboardSummary>("/dashboard/summary");

export const getProgressOverview = () =>
  getJson<ProgressOverview>("/progress/overview");

export const getProjects = () => getJson<ProjectList>("/projects");

export const getUserSettings = () => getJson<UserSettings>("/settings");

export interface Profile {
  full_name?: string | null;
  language?: string | null;
  career_slug?: string | null;
  skill_level?: string | null;
  learning_style?: string | null;
  daily_hours?: number | null;
  target_duration?: number | null;
}

export async function getProfileServer(): Promise<Profile | null> {
  try {
    const res = await authedFetch("/profile/me");
    return res.ok ? ((await res.json()) as Profile) : null;
  } catch {
    return null;
  }
}
