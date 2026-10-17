import { api } from "./client";

/**
 * Persists a learning unit's completed flag.
 *
 * NOTE: the existing web app never marks units complete, so this endpoint
 * path is inferred from the task one (`PATCH /roadmaps/tasks/:id`) and has
 * NOT been confirmed against the backend. It is isolated here so it's a
 * one-line change if the real route differs.
 */
export async function setUnitCompleted(unitId: string, completed: boolean) {
  await api.patch(`/roadmaps/units/${unitId}`, { completed });
}
