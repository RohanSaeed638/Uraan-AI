import { getRoadmapDetails } from "@/lib/server/data";
import { flattenUnits } from "@/lib/units";

import ProjectsClient from "./ProjectsClient";

export default async function ProjectsPage() {
  const roadmaps = await getRoadmapDetails();

  const projects = flattenUnits(roadmaps)
    .filter((c) => c.unit.type?.toLowerCase() === "project")
    .map((c) => ({
      id: c.unit.id,
      title: c.unit.title,
      description: c.unit.description,
      minutes: c.unit.estimated_minutes,
      completed: c.unit.completed,
      context: `${c.taskTitle} · ${c.roadmapTitle}`,
      href: `/roadmaps/${c.roadmapId}/task/${c.taskId}/learn/${c.unit.id}`,
    }));

  return <ProjectsClient projects={projects} />;
}
