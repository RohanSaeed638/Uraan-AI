import { create } from "zustand";
import { User } from "@supabase/supabase-js";

import { AuthState } from "@/types/auth";

export const useAuthStore = create<AuthState>((set) => ({
  user: null,

  loading: false,

  setUser: (user: User | null) =>
    set({
      user,
    }),

  setLoading: (loading: boolean) =>
    set({
      loading,
    }),

  logout: () =>
    set({
      user: null,
    }),
}));