import { api } from "./client";
import { Portfolio, PortfolioProject } from "@/types/api";

export type ProjectInput = Partial<
  Pick<
    PortfolioProject,
    "title" | "description" | "repo_url" | "live_url" | "tech" | "visible"
  >
>;

export async function updatePortfolio(changes: {
  headline?: string | null;
  bio?: string | null;
  slug?: string;
  is_public?: boolean;
}) {
  const { data } = await api.patch<Portfolio>("/portfolio", changes);
  return data;
}

export async function setChecklistItem(item_id: string, done: boolean) {
  const { data } = await api.patch<Portfolio>("/portfolio/checklist", {
    item_id,
    done,
  });
  return data;
}

export async function createProject(
  input: ProjectInput & { source_unit_id?: string }
) {
  const { data } = await api.post<PortfolioProject>("/portfolio/projects", input);
  return data;
}

export async function updateProject(id: string, input: ProjectInput) {
  const { data } = await api.patch<PortfolioProject>(
    `/portfolio/projects/${id}`,
    input
  );
  return data;
}

export async function deleteProject(id: string) {
  await api.delete(`/portfolio/projects/${id}`);
}

export async function draftProjectDescription(id: string) {
  const { data } = await api.post<{ description: string }>(
    `/portfolio/projects/${id}/draft`
  );
  return data.description;
}
