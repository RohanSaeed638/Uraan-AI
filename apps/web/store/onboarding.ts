import { create } from "zustand";

interface OnboardingState {
  step: number;

  language: string;

  career: string;

  skillLevel: string;

  dailyHours: number;

  targetDuration: number;

  learningStyle: string;

  next: () => void;

  previous: () => void;

  update: (data: Partial<OnboardingState>) => void;

  reset: () => void;
}

const initialState = {
  step: 1,
  language: "en",
  career: "",
  skillLevel: "",
  dailyHours: 2,
  targetDuration: 12,
  learningStyle: "",
};

export const useOnboardingStore = create<OnboardingState>((set) => ({
  ...initialState,

  next: () => set((state) => ({ step: state.step + 1 })),

  previous: () => set((state) => ({ step: state.step - 1 })),

  update: (data) => set((state) => ({ ...state, ...data })),

  reset: () => set(initialState),
}));