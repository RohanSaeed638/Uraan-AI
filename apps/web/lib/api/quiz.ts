import { api } from "./client";
import { QuizQuestion, QuizResult } from "@/types/api";

export async function getQuiz(taskId: string) {
  const { data } = await api.get<QuizQuestion[]>(`/tasks/${taskId}/quiz`);
  return data;
}

export async function submitQuiz(
  taskId: string,
  answers: { question_id: string; selected_option: number }[]
) {
  const { data } = await api.post<QuizResult>(`/tasks/${taskId}/quiz/submit`, {
    answers,
  });
  return data;
}
