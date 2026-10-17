// import { createClient } from "@/lib/supabase/client";

// const supabase = createClient();

// export async function register(
//   email: string,
//   password: string,
//   fullName: string
// ) {
//   return supabase.auth.signUp({
//     email,
//     password,
//     options: {
//       data: {
//         full_name: fullName,
//       },
//     },
//   });
// }

// export async function login(email: string, password: string) {
//   return supabase.auth.signInWithPassword({
//     email,
//     password,
//   });
// }

// export async function logout() {
//   return supabase.auth.signOut();
// }

import { createClient } from "@/lib/supabase/client";

const supabase = createClient();

export class AuthService {
  async register(
  fullName: string,
  email: string,
  password: string
  ) {
    return await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
        data: {
        full_name: fullName,
        },
      },
    });
  }

  async login(email: string, password: string) {
    return await supabase.auth.signInWithPassword({
      email,

      password,
    });
  }

  async loginWithOAuth(provider: "google" | "github") {
    return await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
  }

  async resetPassword(email: string) {
    return await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    });
  }

  async updateFullName(fullName: string) {
    return await supabase.auth.updateUser({
      data: { full_name: fullName },
    });
  }

  async logout() {
    await supabase.auth.signOut();
  }

  async getUser() {
    return await supabase.auth.getUser();
  }

  async session() {
    return await supabase.auth.getSession();
  }
}

export const authService = new AuthService();