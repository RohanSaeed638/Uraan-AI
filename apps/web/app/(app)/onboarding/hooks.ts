import { useMutation } from "@tanstack/react-query";

import { updateProfile } from "./api";

export function useCompleteOnboarding() {
  return useMutation({
    mutationFn: updateProfile,
  });
}