/** Response shapes for the aggregate backend endpoints. */

export interface DashboardSummary {
  user: { name: string | null; career_goal: string | null };
  current_roadmap: {
    id: string;
    title: string;
    total_phases: number;
    total_tasks: number;
    completed_tasks: number;
    completion_percentage: number;
  } | null;
  next_learning: {
    roadmap_id: string;
    task_id: string;
    learning_unit_id: string;
    task_title: string;
    learning_unit_title: string;
    learning_unit_type: string;
    estimated_minutes: number | null;
  } | null;
  stats: {
    total_roadmaps: number;
    completed_roadmaps: number;
    total_tasks: number;
    completed_tasks: number;
    remaining_tasks: number;
    total_learning_units: number;
    completed_learning_units: number;
  };
}

export interface CompletionStats {
  total: number;
  completed: number;
  remaining: number;
  completion_percentage: number;
}

export interface ProgressOverview {
  roadmaps: { total: number; completed: number; in_progress: number };
  tasks: CompletionStats;
  learning_units: CompletionStats;
  estimated_completed_learning_hours: number;
  roadmap_progress: {
    roadmap_id: string;
    title: string;
    total_tasks: number;
    completed_tasks: number;
    completion_percentage: number;
    phases: {
      phase_id: string;
      title: string;
      total_tasks: number;
      completed_tasks: number;
      completion_percentage: number;
    }[];
  }[];
}

export interface ProjectItem {
  id: string;
  title: string;
  description: string | null;
  roadmap_id: string;
  roadmap_title: string;
  phase_id: string;
  phase_title: string;
  task_id: string;
  task_title: string;
  estimated_minutes: number | null;
  completed: boolean;
  day: number;
}

export interface ProjectList {
  total: number;
  completed: number;
  pending: number;
  projects: ProjectItem[];
}

export interface UserSettings {
  id: string;
  profile_id: string;
  theme: "light" | "dark" | "system";
  email_notifications: boolean;
  learning_reminders: boolean;
  reminder_time: string;
  timezone: string;
  ai_mentor_enabled: boolean;
}

export interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  order: number;
}

export interface QuizResult {
  attempt_id: string;
  task_id: string;
  total_questions: number;
  correct_answers: number;
  score_percentage: number;
  passed: boolean;
  passing_percentage: number;
  results: {
    question_id: string;
    selected_option: number;
    correct_option: number;
    is_correct: boolean;
    explanation: string | null;
  }[];
}

export interface MentorConversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface MentorMessage {
  id: string;
  role: "user" | "assistant" | string;
  content: string;
  created_at: string;
}

export interface MentorConversationDetail extends MentorConversation {
  messages: MentorMessage[];
}

export interface MentorConversationList {
  conversations: MentorConversation[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
}

export interface MentorSendResult {
  conversation_id: string;
  user_message: MentorMessage;
  assistant_message: MentorMessage;
}
