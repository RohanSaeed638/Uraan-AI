import { api } from "@/lib/api";

import { OnboardingForm } from "./schema";

export async function updateProfile(
  body: OnboardingForm
) {
  const response = await api.put(
    "/profile/me",
    body
  );

  return response.data;
}