import { notFound } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

import RoadmapDetailClient from "./RoadmapDetailClient";
import { Roadmap } from "@/types/roadmap";

/** Changes whenever the plan itself changes (rebuilt, adapted, restored,
 * paused...), so the client component starts over from the new data. Ticking
 * tasks does not change it. */
function contentKey(roadmap: Roadmap) {
  const ids = roadmap.phases.flatMap((p) => p.tasks.map((t) => t.id));

  return [roadmap.status, roadmap.title, roadmap.generation_error ?? "", ids.length, ids[0], ids.at(-1)].join("|");
}

export default async function RoadmapDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const supabase = await createClient();

  async function authHeader() {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    return { Authorization: `Bearer ${session?.access_token}` };
  }

  async function getRoadmap(id: string): Promise<Roadmap | null> {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/roadmaps/${id}`,
      {
        headers: await authHeader(),
        cache: "no-store",
        credentials: "include",
      }
    );

    if (!response.ok) return null;
    return response.json();
  }

  const { id } = await params;
  const roadmap = await getRoadmap(id);

  if (!roadmap) {
    notFound();
  }

  return (
    <main className="mx-auto max-w-5xl">
      <RoadmapDetailClient key={contentKey(roadmap)} roadmap={roadmap} />
    </main>
  );
}
