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

/**
 * Ends the login. The server does the real work (it revokes the session and
 * clears the cookies it reads); the browser client is cleared afterwards so
 * its own copy and any other open tab notice. Neither step can throw, so
 * callers can always carry on to the login page.
 */
let ending = false;

/** True while this tab is signing itself out and about to leave the page. */
export const isEndingSession = () => ending;

async function endSession(scope: "local" | "global") {
  ending = true;

  try {
    await fetch(`/auth/signout?scope=${scope}`, {
      method: "POST",
      credentials: "same-origin",
      cache: "no-store",
    });
  } catch {
    // Offline: the browser-side sign-out below still clears this device.
  }

  try {
    await supabase.auth.signOut({ scope: "local" });
  } catch {
    // Nothing more to clear.
  }

  // The caller redirects next; if that somehow doesn't happen, don't leave
  // the "signing out" state stuck on.
  setTimeout(() => {
    ending = false;
  }, 5000);
}

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

  /** Signs out this device only. */
  async logout() {
    await endSession("local");
  }

  /** Signs out every device, not just this browser. */
  async logoutEverywhere() {
    await endSession("global");
  }

  /** Supabase emails a confirmation link to the new address. */
  async updateEmail(email: string) {
    return await supabase.auth.updateUser(
      { email },
      { emailRedirectTo: `${window.location.origin}/auth/callback` }
    );
  }

  async updatePassword(password: string) {
    return await supabase.auth.updateUser({ password });
  }

  /** Confirms the current password, so a stolen session can't change it. */
  async verifyPassword(email: string, password: string) {
    return await supabase.auth.signInWithPassword({ email, password });
  }

  async getUser() {
    return await supabase.auth.getUser();
  }

  async session() {
    return await supabase.auth.getSession();
  }
}

export const authService = new AuthService();