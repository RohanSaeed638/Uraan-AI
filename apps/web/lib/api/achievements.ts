import { api } from "./client";

export interface AchievementItem {
  code: string;
  title: string;
  description: string;
  category: "learning" | "streak" | "projects" | "practice" | "career";
  icon: string;
  xp_reward: number;
  unlocked: boolean;
  unlocked_at: string | null;
  current: number;
  target: number;
}

export interface Boss {
  unit_id: string;
  title: string;
  task_title: string;
  roadmap_id: string;
  task_id: string;
  bonus_xp: number;
  defeated: boolean;
  days_left: number;
}

export interface AchievementsResult {
  items: AchievementItem[];
  unlocked_count: number;
  total: number;
  boss: Boss | null;
}

export type ReadinessKey =
  | "tasks"
  | "projects"
  | "consistency"
  | "interviews"
  | "portfolio";

export interface Readiness {
  score: number;
  level: "getting_started" | "building" | "almost_there" | "job_ready";
  components: { key: ReadinessKey; weight: number; value: number; points: number }[];
  tips: { key: ReadinessKey; action: string; count: number; href: string }[];
}

export const getAchievements = () =>
  api.get<AchievementsResult>("/achievements").then((r) => r.data);

export const getReadiness = () =>
  api.get<Readiness>("/readiness").then((r) => r.data);
