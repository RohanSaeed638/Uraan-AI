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

export interface Gamification {
  xp: number;
  level: number;
  xp_into_level: number;
  xp_per_level: number;
  streak_days: number;
  active_today: boolean;
  weekly_xp: number;
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
  show_on_leaderboard: boolean;
}

export interface AppNotification {
  id: string;
  type: string;
  title: string;
  body: string;
  url: string | null;
  read: boolean;
  created_at: string;
}

export interface NotificationList {
  notifications: AppNotification[];
  unread_count: number;
}

export type Difficulty = "beginner" | "intermediate" | "advanced";

export interface InterviewTurn {
  order: number;
  question: string;
  answer: string | null;
  feedback: string | null;
  technical_score: number | null;
  communication_score: number | null;
  confidence_score: number | null;
}

export interface InterviewSession {
  id: string;
  role: string;
  difficulty: Difficulty;
  status: "in_progress" | "completed";
  overall_score: number | null;
  averages: {
    technical: number;
    communication: number;
    confidence: number;
  } | null;
  summary: {
    strengths: string[];
    improvements: string[];
    next_steps: string[];
  } | null;
  answered: number;
  total: number;
  created_at: string;
  turns: InterviewTurn[];
}

export type InterviewListItem = Omit<
  InterviewSession,
  "averages" | "summary" | "turns"
>;

export interface PortfolioProject {
  id: string;
  source_unit_id: string | null;
  title: string;
  description: string | null;
  repo_url: string | null;
  live_url: string | null;
  tech: string[];
  visible: boolean;
}

export interface Portfolio {
  headline: string | null;
  bio: string | null;
  slug: string | null;
  is_public: boolean;
  projects: PortfolioProject[];
  checklist: { id: string; label: string; done: boolean }[];
  suggestions: { unit_id: string; title: string; task_title: string }[];
}

export interface PublicPortfolio {
  name: string;
  headline: string | null;
  bio: string | null;
  projects: Pick<
    PortfolioProject,
    "title" | "description" | "repo_url" | "live_url" | "tech"
  >[];
}

export type DocumentKind = "resume" | "cover_letter" | "linkedin_summary";

export interface CareerDocument {
  id: string;
  kind: DocumentKind;
  title: string;
  target_role: string | null;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface CalendarDay {
  date: string;
  day: number;
  total_estimated_minutes: number;
  units: {
    id: string;
    task_id: string;
    task_title: string;
    title: string;
    type: string;
    estimated_minutes: number | null;
    completed: boolean;
  }[];
}

export interface CalendarSchedule {
  roadmap_id: string | null;
  roadmap_title: string | null;
  today: string;
  days: CalendarDay[];
}

export type LeaderboardPeriod = "weekly" | "all_time";

export interface Leaderboard {
  period: LeaderboardPeriod;
  entries: {
    rank: number;
    display_name: string;
    xp: number;
    level: number;
    is_me: boolean;
  }[];
  me: { xp: number; rank: number | null; on_leaderboard: boolean };
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

export interface ProfileData {
  id: string;
  full_name: string;
  language: string;
  country: string | null;
  timezone: string | null;
  career_slug: string | null;
  skill_level: "beginner" | "intermediate" | "advanced" | null;
  learning_style: "reading" | "reading_video" | "reading_video_project" | null;
  career_stage:
    | "beginner"
    | "job_ready"
    | "student"
    | "professional"
    | "career_switcher"
    | null;
  daily_hours: number;
  target_duration: number;
  learning_goal: string | null;
  onboarding_completed: boolean;
  streak_days: number;
  xp: number;
  created_at: string | null;
}

export type ProfileChanges = Partial<
  Omit<
    ProfileData,
    "id" | "onboarding_completed" | "streak_days" | "xp" | "created_at"
  >
>;
