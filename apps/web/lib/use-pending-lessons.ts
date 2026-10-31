"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { generateLearningPlan } from "@/lib/api/units";
import { LearningUnit } from "@/types/roadmap";

const POLL_MS = 5000;

/**
 * A task's plan is saved in seconds and its lessons are written behind it. While
 * any is still being written this reloads the page's data every few seconds (and
 * nudges the server, which restarts writing that was interrupted), so lessons
 * appear as they finish.
 */
export function usePendingLessons(taskId: string, units: LearningUnit[]) {
  const router = useRouter();

  const waiting = units.filter((u) => u.status === "pending" || u.status === "writing").length;
  const failed = units.filter((u) => u.status === "failed").length;

  useEffect(() => {
    if (waiting === 0) return;

    const timer = setInterval(async () => {
      try {
        await generateLearningPlan(taskId);
      } catch {
        // The next tick tries again.
      }

      router.refresh();
    }, POLL_MS);

    return () => clearInterval(timer);
  }, [waiting, taskId, router]);

  return { waiting, failed, ready: units.length - waiting - failed, total: units.length };
}
