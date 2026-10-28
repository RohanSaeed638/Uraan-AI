import { User } from "@supabase/supabase-js";

export interface AuthState {
  user: User | null;

  loading: boolean;

  setUser: (user: User | null) => void;

  setLoading: (loading: boolean) => void;

  logout: () => void;
}