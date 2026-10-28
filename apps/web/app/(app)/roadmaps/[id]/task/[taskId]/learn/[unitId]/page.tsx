import { notFound } from "next/navigation";

import { createClient } from "@/lib/supabase/server";
import UnitViewer from "./UnitViewer";

interface PageProps {
  params: Promise<{ id: string; taskId: string; unitId: string }>;
}

export default async function LearnUnitPage({ params }: PageProps) {
  const { id: roadmapId, taskId, unitId } = await params;

  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) notFound();

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/tasks/${taskId}`,
    {
      headers: { Authorization: `Bearer ${session.access_token}` },
      cache: "no-store",
    }
  );

  if (!response.ok) notFound();

  const task = await response.json();

  if (!(task.learning_units ?? []).some((u: { id: string }) => u.id === unitId)) {
    notFound();
  }

  return <UnitViewer roadmapId={roadmapId} task={task} initialUnitId={unitId} />;
}
