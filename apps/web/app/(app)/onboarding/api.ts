import { api } from "@/lib/api";

import { OnboardingForm } from "./types";

export async function updateProfile(
  body: OnboardingForm
) {
  const response = await api.put(
    "/profile/me",
    body
  );

  return response.data;
}