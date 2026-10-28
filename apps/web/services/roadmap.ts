import { translateApiMessage } from "@/lib/api-errors";
import axios from "axios";
import { createClient } from "@/lib/supabase/client";
import { RoadmapJobStatus } from "@/types/roadmap";

const API = process.env.NEXT_PUBLIC_API_URL;
const supabase = createClient();

async function authHeader() {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  return {
    Authorization: `Bearer ${session?.access_token}`,
  };
}

export interface GenerateRoadmapPayload {
  career_slug: string;
  career_stage: string;
  skill_level: string;
  learning_goal: string;
  daily_hours: number;
  target_duration: number;
  learning_style: string;
}

export async function generateRoadmap(payload: GenerateRoadmapPayload) {
  return axios.post(
    `${API}/roadmaps/generate`,
    payload,
    {
      headers: await authHeader(),
    }
  );
}

export async function getRoadmap() {
  return axios.get(`${API}/roadmaps/current`, {
    headers: await authHeader(),
  });
}

/**
 * Waits for a roadmap that is being built, rebuilt or adapted in the
 * background. Resolves with the final status ("failed" included: the caller
 * decides what to show); rejects only if it takes too long or the status
 * cannot be read several times in a row.
 */
export async function waitForRoadmap(
  id: string,
  { intervalMs = 2500, timeoutMs = 5 * 60 * 1000 } = {}
): Promise<RoadmapJobStatus> {
  const started = Date.now();
  let misses = 0;

  while (Date.now() - started < timeoutMs) {
    try {
      const { data } = await axios.get<RoadmapJobStatus>(
        `${API}/roadmaps/${id}/status`,
        { headers: await authHeader() }
      );

      misses = 0;

      if (data.status !== "generating") return data;
    } catch (error) {
      // A dropped request should not abandon a roadmap that is still being
      // built; give up only after a run of failures.
      if (++misses >= 5) throw error;
    }

    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  throw new Error(
    translateApiMessage("This is taking longer than expected. Check My Roadmaps in a minute.")
  );
}

/** A background roadmap job ended in failure; the message is safe to show. */
export class RoadmapJobError extends Error {}

/** `waitForRoadmap`, turning a failed job into a `RoadmapJobError`. */
export async function finishRoadmap(id: string): Promise<RoadmapJobStatus> {
  const result = await waitForRoadmap(id);

  if (result.status === "failed") {
    throw new RoadmapJobError(
      translateApiMessage(
        result.error ?? "We could not create your roadmap. Please try again."
      )
    );
  }

  return result;
}
