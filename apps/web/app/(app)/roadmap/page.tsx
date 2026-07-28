"use client";

import { useQuery } from "@tanstack/react-query";
import { getRoadmap } from "@/services/roadmap";

export default function RoadmapPage() {

  const { data, isLoading } = useQuery({
    queryKey: ["roadmap"],
    queryFn: getRoadmap,
  });

  if (isLoading) return <div>Loading...</div>;

  const roadmap = data?.data;

  return (
    <div>
      <h1>{roadmap.title}</h1>

      {roadmap.phases.map((phase: any) => (
        <div key={phase.id}>
          <h2>{phase.title}</h2>

          {phase.tasks.map((task: any) => (
            <div key={task.id}>
              {task.title}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}