import { api } from "./client";

export type SearchKind =
  | "roadmap"
  | "task"
  | "lesson"
  | "career"
  | "resource"
  | "document"
  | "conversation";

export interface SearchHit {
  kind: SearchKind;
  id: string;
  title: string;
  subtitle: string | null;
  /** Where clicking the result goes (a path inside the app). */
  url: string;
}

export const searchAll = (q: string, signal?: AbortSignal) =>
  api
    .get<{ query: string; results: SearchHit[] }>("/search", { params: { q }, signal })
    .then((r) => r.data.results);
