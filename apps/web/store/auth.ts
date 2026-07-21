// import { create } from "zustand";

// interface AuthStore {
//   user: any;
//   loading: boolean;

//   setUser: (user: any) => void;
// }

// export const useAuthStore = create<AuthStore>((set) => ({
//   user: null,

//   loading: true,

//   setUser: (user) =>
//     set({
//       user,
//       loading: false,
//     }),
// }));


import { create } from "zustand";
import { User } from "@supabase/supabase-js";

import { AuthState } from "@/types/auth";

export const useAuthStore = create<AuthState>((set) => ({
  user: null,

  loading: true,

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