import { api } from "./client";
import {
  AdaptRequest,
  Roadmap,
  RoadmapJobStatus,
  RoadmapVersion,
} from "@/types/roadmap";

export const pauseRoadmap = (id: string) =>
  api.patch<RoadmapJobStatus>(`/roadmaps/${id}/pause`).then((r) => r.data);

export const resumeRoadmap = (id: string) =>
  api.patch<RoadmapJobStatus>(`/roadmaps/${id}/resume`).then((r) => r.data);

/** Starts a rebuild in the background (202); poll with `waitForRoadmap`. */
export const regenerateRoadmap = (id: string) =>
  api.post<RoadmapJobStatus>(`/roadmaps/${id}/regenerate`).then((r) => r.data);

/** Re-plans the unfinished part in the background (202). */
export const adaptRoadmap = (id: string, request: AdaptRequest) =>
  api.post<RoadmapJobStatus>(`/roadmaps/${id}/adapt`, request).then((r) => r.data);

export const listRoadmapVersions = (id: string) =>
  api.get<RoadmapVersion[]>(`/roadmaps/${id}/versions`).then((r) => r.data);

export const restoreRoadmapVersion = (id: string, versionId: string) =>
  api
    .post<Roadmap>(`/roadmaps/${id}/versions/${versionId}/restore`)
    .then((r) => r.data);
