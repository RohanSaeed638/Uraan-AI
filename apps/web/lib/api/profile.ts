import { api } from "./client";
import { OnboardingForm } from "@/app/(app)/onboarding/types";
import { ProfileData, ProfileChanges } from "@/types/api";

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

/** Edits only the fields given (`PATCH /profile/me`). */
export async function patchProfile(changes: ProfileChanges) {
  const response = await api.patch<ProfileData>("/profile/me", changes);

  return response.data;
}
