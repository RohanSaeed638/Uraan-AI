export interface RoadmapTask {
  id: string;
  title: string;
  description: string;
  estimated_hours: number;
  resource_links?: string[] | null;
  completed: boolean;
  order: number;
}

export interface RoadmapPhase {
  id: string;
  title: string;
  description: string;
  duration_weeks: number;
  order: number;
  tasks: RoadmapTask[];
}

export type RoadmapStatus =
  | "pending"
  | "generating"
  | "active"
  | "completed"
  | "archived";

export interface Roadmap {
  id: string;
  title: string;
  description: string;
  status: RoadmapStatus;
  created_at: string;
  updated_at: string;
  phases: RoadmapPhase[];
}

export interface RoadmapSummary {
  id: string;
  title: string;
  description: string;
  status: RoadmapStatus;
  progress: number;
  completed_tasks: number;
  total_tasks: number;
  updated_at: string;
}

export enum CareerStage {
  BEGINNER = "beginner",
  JOB_READY = "job_ready",
  STUDENT = "student",
  PROFESSIONAL = "professional",
  CAREER_SWITCHER = "career_switcher",
}

export enum SkillLevel {
  BEGINNER = "beginner",
  INTERMEDIATE = "intermediate",
  ADVANCED = "advanced",
}

export enum LearningStyle {
  VIDEO = "video",
  READING = "reading",
  PROJECT = "project",
  MIXED = "mixed",
}

export interface GenerateRoadmapFormValues {
  career_slug: string;
  career_stage: CareerStage;
  skill_level: SkillLevel;
  learning_goal: string;
  daily_hours: number;
  target_duration: number;
  learning_style: LearningStyle;
}