export interface RoadmapTask {
  id: string;
  title: string;
  description: string;
  estimated_hours: number;
  resource_url?: string | null;
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