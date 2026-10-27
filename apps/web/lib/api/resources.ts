import { api } from "./client";

export interface LibraryResource {
  id: string;
  title: string;
  url: string;
  type: "course" | "video" | "docs" | "book" | "practice" | string;
  provider: string | null;
  description: string | null;
  is_free: boolean;
  difficulty: "beginner" | "intermediate" | "advanced" | null;
  career_slugs: string[];
  avg_rating: number | null;
  rating_count: number;
  bookmarked: boolean;
  my_rating: number | null;
}

export interface ResourceList {
  items: LibraryResource[];
  total: number;
  page: number;
  page_size: number;
}

export interface ResourceFilters {
  q?: string;
  career?: string;
  type?: string;
  difficulty?: string;
  free_only?: boolean;
  bookmarked?: boolean;
  sort?: "recommended" | "title" | "newest";
}

export async function listResources(filters: ResourceFilters = {}) {
  const params: Record<string, string | number | boolean> = { page_size: 50 };

  if (filters.q?.trim()) params.q = filters.q.trim();
  if (filters.career) params.career = filters.career;
  if (filters.type) params.type = filters.type;
  if (filters.difficulty) params.difficulty = filters.difficulty;
  if (filters.free_only) params.free_only = true;
  if (filters.bookmarked) params.bookmarked = true;
  if (filters.sort) params.sort = filters.sort;

  const response = await api.get<ResourceList>("/resources", { params });

  return response.data;
}

export const recommendedResources = (taskId: string, limit = 4) =>
  api
    .get<LibraryResource[]>("/resources/recommended", {
      params: { task_id: taskId, limit },
    })
    .then((r) => r.data);

export const setBookmark = (id: string, saved: boolean) =>
  (saved
    ? api.post<LibraryResource>(`/resources/${id}/bookmark`)
    : api.delete<LibraryResource>(`/resources/${id}/bookmark`)
  ).then((r) => r.data);

/** `rating: null` removes the learner's rating. */
export const setRating = (id: string, rating: number | null) =>
  (rating === null
    ? api.delete<LibraryResource>(`/resources/${id}/rating`)
    : api.put<LibraryResource>(`/resources/${id}/rating`, { rating })
  ).then((r) => r.data);
