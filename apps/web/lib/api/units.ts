import { api } from "./client";

/** Persists a learning unit's completed flag (`PATCH /learning-units/:id`). */
export async function setUnitCompleted(unitId: string, completed: boolean) {
  await api.patch(`/learning-units/${unitId}`, { completed });
}

/**
 * Asks the server to write this task's lessons if it has none. Safe to call
 * more than once: a task that already has lessons is returned unchanged.
 * Generation can take half a minute.
 */
export async function generateLearningPlan(taskId: string) {
  await api.post(`/tasks/${taskId}/learning-plan`, undefined, {
    timeout: 120_000,
  });
}
