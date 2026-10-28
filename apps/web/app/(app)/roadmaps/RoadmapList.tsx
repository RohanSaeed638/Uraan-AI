import RoadmapCard from "./RoadmapCard";

import { RoadmapSummary } from "@/types/roadmap";

interface Props {
  roadmaps: RoadmapSummary[];
}

export default function RoadmapList({
  roadmaps,
}: Props) {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      {roadmaps.map((roadmap) => (
        <RoadmapCard
          key={roadmap.id}
          roadmap={roadmap}
        />
      ))}
    </div>
  );
}