import { api } from "./client";
import {
  CareerDetail,
  CareerFilters,
  CareerList,
  CareerRecommendation,
  RecommendAnswers,
} from "@/types/api";

export async function listCareers(filters: CareerFilters = {}) {
  const params: Record<string, string | number> = { page_size: 50 };

  if (filters.search?.trim()) params.search = filters.search.trim();
  if (filters.difficulty) params.difficulty = filters.difficulty;
  if (filters.demand) params.demand = filters.demand;
  if (filters.min_salary) params.min_salary = filters.min_salary;

  const response = await api.get<CareerList>("/careers", { params });

  return response.data;
}

export async function compareCareers(slugs: string[]) {
  const response = await api.post<{ careers: CareerDetail[] }>(
    "/careers/compare",
    { slugs }
  );

  return response.data.careers;
}

export async function recommendCareers(answers: RecommendAnswers) {
  const response = await api.post<{ recommendations: CareerRecommendation[] }>(
    "/careers/recommend",
    answers
  );

  return response.data.recommendations;
}
