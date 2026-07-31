import { createClient } from "@/lib/supabase/server";

import RoadmapList from "./RoadmapList";
import EmptyState from "./EmptyState";
import GenerateRoadmapButton from "./GenerateRoadmapButton";

export default async function RoadmapPage() {

  const supabase = await createClient();

  const {
    data: { session },
  } = await supabase.auth.getSession();

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/roadmaps`,
    {
      headers: {
        Authorization: `Bearer ${session?.access_token}`,
      },
      cache: "no-store",
    }
  );
  const roadmaps = await response.json();
  
  if(roadmaps?.success === false) {
    return (
      <main className="mx-auto max-w-6xl p-8">
        <div className="mb-10 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold">

              My Roadmaps
            </h1>

            <p className="mt-2 text-muted-foreground">
              Track all your career journeys.
            </p>
          </div>
          <GenerateRoadmapButton/>
        </div>
        <EmptyState />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-6xl p-8">

      <div className="mb-10 flex items-center justify-between">

        <div>

          <h1 className="text-4xl font-bold">
            My Roadmaps
          </h1>

          <p className="mt-2 text-muted-foreground">
            Track all your career journeys.
          </p>

        </div>

         <GenerateRoadmapButton/>

      </div>

      {roadmaps.length === 0 ? (
        <EmptyState />
      ) : (
        <RoadmapList roadmaps={roadmaps} />
      )}

    </main>
  );
}