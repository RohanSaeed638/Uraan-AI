import { api } from "./client";

export interface AdminCounts {
  users: number;
  new_users_7d: number;
  active_users_7d: number;
  roadmaps: number;
  lessons_completed: number;
  tasks_completed: number;
  mentor_messages: number;
}

export interface AdminStats {
  counts: AdminCounts;
  days: number;
  ai_requests: number;
  ai_failures: number;
  ai_by_purpose: {
    purpose: string;
    requests: number;
    failures: number;
    failure_rate: number;
    avg_latency_ms: number | null;
  }[];
  ai_by_provider: { provider: string; requests: number; failures: number }[];
  recent_failures: { at: string; purpose: string; provider: string; error_type: string | null }[];
}

export interface AdminUser {
  id: string;
  name: string;
  email: string | null;
  role: "user" | "admin";
  language: string;
  career_slug: string | null;
  xp: number;
  streak_days: number;
  roadmaps: number;
  created_at: string;
  last_activity_date: string | null;
}

export interface CareerRow {
  id: string;
  slug: string;
  name: string;
  category: string | null;
  difficulty: string | null;
  market_demand: string | null;
  is_active: boolean;
  skills: number;
  resources: number;
}

export interface CareerResourceInput {
  title: string;
  type: string;
  provider: string | null;
  url: string;
  is_free: boolean;
  difficulty: string | null;
}

export interface CareerInput {
  name: string;
  description: string;
  category: string | null;
  icon: string | null;
  color: string | null;
  difficulty: string | null;
  estimated_months: number | null;
  salary_min_pkr: number | null;
  salary_max_pkr: number | null;
  market_demand: string | null;
  is_active: boolean;
  skills: { name: string }[];
  resources: CareerResourceInput[];
}

export interface AdminCareer extends CareerInput {
  id: string;
  slug: string;
}

export interface ResourceInput {
  title: string;
  url: string;
  type: string;
  provider: string | null;
  description: string | null;
  is_free: boolean;
  difficulty: string | null;
  career_slugs: string[];
  language: string;
  is_active: boolean;
}

export interface AdminResource extends ResourceInput {
  id: string;
}

export interface AnnouncementRow {
  id: string;
  title: string;
  body: string;
  level: "info" | "warning";
  is_active: boolean;
  starts_at: string | null;
  ends_at: string | null;
  notified: number;
  created_at: string;
}

export interface AuditEntry {
  id: string;
  at: string;
  actor: string;
  action: string;
  target_type: string;
  target_id: string | null;
  summary: string;
  changes: Record<string, [unknown, unknown]> | null;
}

export const listAdminUsers = async (params: { search?: string; limit?: number; offset?: number }) =>
  (await api.get<{ items: AdminUser[]; total: number }>("/admin/users", { params })).data;

export const setUserRole = async (id: string, role: "user" | "admin") =>
  (await api.patch<{ id: string; role: string }>(`/admin/users/${id}/role`, { role })).data;

export const listAdminCareers = async () => (await api.get<CareerRow[]>("/admin/careers")).data;
export const getAdminCareer = async (id: string) => (await api.get<AdminCareer>(`/admin/careers/${id}`)).data;
export const createCareer = async (data: CareerInput & { slug: string }) =>
  (await api.post<AdminCareer>("/admin/careers", data)).data;
export const updateCareer = async (id: string, data: CareerInput) =>
  (await api.put<AdminCareer>(`/admin/careers/${id}`, data)).data;

export const listAdminResources = async (params: {
  search?: string;
  active?: boolean;
  limit?: number;
  offset?: number;
}) => (await api.get<{ items: AdminResource[]; total: number }>("/admin/resources", { params })).data;
export const createResource = async (data: ResourceInput) =>
  (await api.post<AdminResource>("/admin/resources", data)).data;
export const updateResource = async (id: string, data: ResourceInput) =>
  (await api.put<AdminResource>(`/admin/resources/${id}`, data)).data;

export const listAnnouncements = async () => (await api.get<AnnouncementRow[]>("/admin/announcements")).data;
export const publishAnnouncement = async (data: {
  title: string;
  body: string;
  level: "info" | "warning";
  ends_at: string | null;
  notify: boolean;
}) => (await api.post<AnnouncementRow>("/admin/announcements", data)).data;
export const updateAnnouncement = async (id: string, data: { is_active?: boolean; ends_at?: string | null }) =>
  (await api.patch<AnnouncementRow>(`/admin/announcements/${id}`, data)).data;

export const listAudit = async (params: { limit?: number; before?: string; action?: string }) =>
  (await api.get<{ items: AuditEntry[]; has_more: boolean }>("/admin/audit", { params })).data;

export interface ActiveAnnouncement {
  id: string;
  title: string;
  body: string;
  level: "info" | "warning";
}

export const getActiveAnnouncements = async () =>
  (await api.get<ActiveAnnouncement[]>("/announcements/active")).data;
