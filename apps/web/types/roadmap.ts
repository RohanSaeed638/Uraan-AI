export interface RoadmapTask {
  id: string;
  title: string;
  description: string;
  estimated_hours: number;
  resource_links?: string[] | null;
  completed: boolean;
  order: number;
  week?: number | null;
  learning_units: LearningUnit[];
}

export interface RoadmapPhase {
  id: string;
  title: string;
  description: string;
  duration_weeks: number;
  milestones?: string[] | null;
  order: number;
  tasks: RoadmapTask[];
}

export type RoadmapStatus =
  | "pending"
  | "generating"
  | "active"
  | "paused"
  | "completed"
  | "archived"
  | "failed";

export interface Roadmap {
  id: string;
  title: string;
  description: string;
  status: RoadmapStatus;
  generation_error?: string | null;
  daily_hours?: number | null;
  target_duration?: number | null;
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
  READING_VIDEO = "reading_video",
  READING = "reading",
  READING_VIDEO_PROJECT = "reading_video_project",
}

// export type LearningStyle =
//   | "reading"
//   | "reading_video"
//   | "reading_video_project";

export interface GenerateRoadmapFormValues {
  career_slug: string;
  career_stage: CareerStage;
  skill_level: SkillLevel;
  learning_goal: string;
  daily_hours: number;
  target_duration: number;
  learning_style: LearningStyle;
}

export type LearningUnitType =
  | "reading"
  | "video"
  | "project"
  | "exercise";

/** Extra data on a coding exercise (the problem itself is `content`). */
export interface ExerciseDetails {
  language: string;
  starter_code: string;
  hints: string[];
  solution: string;
  expected_output?: string | null;
}

/** Extra data on a project lesson. */
export interface ProjectDetails {
  difficulty: "beginner" | "intermediate" | "advanced" | null;
  skills: string[];
  portfolio_value: string | null;
}

export interface LearningUnit {
  id: string;
  task_id: string;

  day: number;
  order: number;

  type: LearningUnitType;

  title: string;
  description: string | null;
  content: string | null;

  resource_url: string | null;

  /** ExerciseDetails for an exercise, ProjectDetails for a project. */
  details?: Record<string, unknown> | null;

  estimated_minutes: number | null;

  completed: boolean;
}

/** What the browser polls while a roadmap is being built or rebuilt. */
export interface RoadmapJobStatus {
  id: string;
  title: string;
  status: RoadmapStatus;
  error: string | null;
}

export type AdaptReason = "study_time" | "behind" | "goal";

export interface AdaptRequest {
  reason: AdaptReason;
  daily_hours?: number;
  months_left?: number;
  note?: string;
}

export interface RoadmapVersion {
  id: string;
  version_number: number;
  reason: "regenerate" | "adapt" | "restore";
  created_at: string;
  phases: number;
  tasks: number;
  completed: number;
}
