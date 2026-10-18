import { api } from "./client";
import { Difficulty, InterviewSession, InterviewTurn } from "@/types/api";

export async function startInterview(role: string, difficulty?: Difficulty) {
  const { data } = await api.post<InterviewSession>("/interviews", {
    role,
    difficulty,
  });
  return data;
}

export async function answerQuestion(
  sessionId: string,
  order: number,
  answer: string
) {
  const { data } = await api.post<InterviewTurn>(
    `/interviews/${sessionId}/turns/${order}/answer`,
    { answer }
  );
  return data;
}

export async function finishInterview(sessionId: string) {
  const { data } = await api.post<InterviewSession>(
    `/interviews/${sessionId}/finish`
  );
  return data;
}

export async function deleteInterview(sessionId: string) {
  await api.delete(`/interviews/${sessionId}`);
}
