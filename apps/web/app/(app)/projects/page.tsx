import { getProjects } from "@/lib/server/data";

import ProjectsClient from "./ProjectsClient";

export default async function ProjectsPage() {
  const data = await getProjects();

  const projects = (data?.projects ?? []).map((p) => ({
    id: p.id,
    title: p.title,
    description: p.description,
    minutes: p.estimated_minutes,
    completed: p.completed,
    difficulty: p.difficulty ?? null,
    skills: p.skills ?? [],
    portfolioValue: p.portfolio_value ?? null,
    context: `${p.task_title} · ${p.roadmap_title}`,
    href: `/roadmaps/${p.roadmap_id}/task/${p.task_id}/learn/${p.id}`,
  }));

  return <ProjectsClient projects={projects} />;
}
