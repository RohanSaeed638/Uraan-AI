import { create } from "zustand";

interface AuthStore {
  user: any;
  loading: boolean;

  setUser: (user: any) => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,

  loading: true,

  setUser: (user) =>
    set({
      user,
      loading: false,
    }),
}));