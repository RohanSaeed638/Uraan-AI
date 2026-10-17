import { createClient } from "@/lib/supabase/server";

import RoadmapList from "./RoadmapList";
import EmptyState from "./EmptyState";
import GenerateRoadmapButton from "./GenerateRoadmapButton";
import { RoadmapSummary } from "@/types/roadmap";

export default async function RoadmapPage() {
  const supabase = await createClient();

  const {
    data: { session },
  } = await supabase.auth.getSession();

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/roadmaps`,
    {
      headers: { Authorization: `Bearer ${session?.access_token}` },
      cache: "no-store",
    }
  );
  const data = await response.json();
  const roadmaps: RoadmapSummary[] = Array.isArray(data) ? data : [];

  return (
    <main className="mx-auto max-w-6xl">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="font-heading text-3xl font-bold">My Roadmaps</h1>
          <p className="mt-1 text-muted-foreground">
            Track all your career journeys.
          </p>
        </div>
        <GenerateRoadmapButton />
      </div>

      {roadmaps.length === 0 ? (
        <EmptyState />
      ) : (
        <RoadmapList roadmaps={roadmaps} />
      )}
    </main>
  );
}
