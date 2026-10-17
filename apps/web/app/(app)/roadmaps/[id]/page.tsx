import { notFound } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

import RoadmapDetailClient from "./RoadmapDetailClient";
import { Roadmap } from "@/types/roadmap";

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
      <RoadmapDetailClient roadmap={roadmap} />
    </main>
  );
}
