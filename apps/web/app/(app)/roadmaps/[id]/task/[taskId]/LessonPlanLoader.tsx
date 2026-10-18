"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { BookOpen, FolderKanban, Loader2, PlayCircle } from "lucide-react";

import { generateLearningPlan } from "@/lib/api/units";

import { Button } from "@/components/ui/button";

function errorMessage(error: unknown) {
  const detail = (error as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;

  return typeof detail === "string"
    ? detail
    : "We couldn't prepare the lessons. Please try again.";
}

/**
 * Shown for a task with no lessons yet. Asks the server to write them, then
 * reloads the page. A failure is shown with a button instead of retrying on
 * its own, because each attempt costs an AI request.
 */
export default function LessonPlanLoader({ taskId }: { taskId: string }) {
  const router = useRouter();
  const started = useRef(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    try {
      await generateLearningPlan(taskId);
      router.refresh();
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function retry() {
    setError(null);
    run();
  }

  return (
    <section className="flex flex-col items-center rounded-xl border bg-card px-6 py-14 text-center">
      {error ? (
        <>
          <h2 className="text-lg font-semibold">Lessons aren&apos;t ready</h2>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">{error}</p>
          <Button className="mt-5" onClick={retry}>
            Try again
          </Button>
        </>
      ) : (
        <>
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <h2 className="mt-5 text-lg font-semibold">
            Preparing your lessons
          </h2>
          <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">
            We&apos;re writing a day-by-day plan for this task. It usually takes
            20 to 40 seconds, and you only wait the first time.
          </p>
          <div className="mt-6 flex gap-5 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <BookOpen className="h-4 w-4" /> Reading
            </span>
            <span className="flex items-center gap-1.5">
              <PlayCircle className="h-4 w-4" /> Videos
            </span>
            <span className="flex items-center gap-1.5">
              <FolderKanban className="h-4 w-4" /> Project
            </span>
          </div>
        </>
      )}
    </section>
  );
}
