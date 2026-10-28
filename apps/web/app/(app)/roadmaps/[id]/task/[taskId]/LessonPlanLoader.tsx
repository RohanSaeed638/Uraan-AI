"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { BookOpen, FolderKanban, Loader2, PlayCircle } from "lucide-react";

import { generateLearningPlan } from "@/lib/api/units";
import { apiErrorMessage } from "@/lib/profile-options";

import { Button } from "@/components/ui/button";

/**
 * Shown for a task with no lessons yet. Asks the server to write them, then
 * reloads the page. A failure is shown with a button instead of retrying on
 * its own, because each attempt costs an AI request.
 */
export default function LessonPlanLoader({ taskId }: { taskId: string }) {
  const router = useRouter();
  const t = useTranslations("lessonPlan");
  const started = useRef(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    try {
      await generateLearningPlan(taskId);
      router.refresh();
    } catch (e) {
      setError(apiErrorMessage(e, t("failed")));
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
          <h2 className="text-lg font-semibold">{t("failedTitle")}</h2>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">{error}</p>
          <Button className="mt-5" onClick={retry}>
            {t("retry")}
          </Button>
        </>
      ) : (
        <>
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <h2 className="mt-5 text-lg font-semibold">
            {t("preparing")}
          </h2>
          <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">
            {t("preparingText")}
          </p>
          <div className="mt-6 flex gap-5 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <BookOpen className="h-4 w-4" /> {t("reading")}
            </span>
            <span className="flex items-center gap-1.5">
              <PlayCircle className="h-4 w-4" /> {t("videos")}
            </span>
            <span className="flex items-center gap-1.5">
              <FolderKanban className="h-4 w-4" /> {t("project")}
            </span>
          </div>
        </>
      )}
    </section>
  );
}
