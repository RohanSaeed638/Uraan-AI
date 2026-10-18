import { api } from "./client";

/** Persists a learning unit's completed flag (`PATCH /learning-units/:id`). */
export async function setUnitCompleted(unitId: string, completed: boolean) {
  await api.patch(`/learning-units/${unitId}`, { completed });
}
