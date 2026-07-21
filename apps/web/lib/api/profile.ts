import { api } from "./client";
import { OnboardingForm } from "@/app/(app)/onboarding/types";

export async function getProfile() {
  const response = await api.get("/profile/me");
  return response.data;
}

export async function updateProfile(
  data: OnboardingForm
) {
  const response = await api.put(
    "/profile/me",
    data
  );

  return response.data;
}