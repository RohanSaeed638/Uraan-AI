import { notFound } from "next/navigation";

import { createClient } from "@/lib/supabase/server";
import TaskLearningPage from "./TaskLearningPage";

interface PageProps {
  params: Promise<{
    id: string;
    taskId: string;
  }>;
}

export default async function Page({
  params,
}: PageProps) {
  const { id:roadmapId, taskId } = await params;
  const supabase = await createClient();

  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) {
    notFound();
  }

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/tasks/${taskId}`,
    {
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
      cache: "no-store",
    }
  );

  if (!response.ok) {
    notFound();
  }

  const task = await response.json();
  console.log("task", task);

  return (
    <TaskLearningPage
      roadmapId={roadmapId}
      task={task}
    />
  );
}