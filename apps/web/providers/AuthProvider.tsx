"use client";

import { useEffect } from "react";

import { createClient } from "@/lib/supabase/client";
import { isEndingSession } from "@/services/auth/auth";

import { useAuthStore } from "@/store/auth";

const PUBLIC_PATHS = ["/login", "/register", "/forgot-password", "/auth", "/p/"];

const isPublicPath = (path: string) =>
  path === "/" || PUBLIC_PATHS.some((p) => path.startsWith(p));

export default function AuthProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = createClient();

  const { setUser } = useAuthStore();

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      setUser(data.user);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      setUser(session?.user ?? null);

      // Signed out in another tab, or the session could no longer be
      // refreshed: leave the signed-in pages instead of showing a dead app.
      if (
        event === "SIGNED_OUT" &&
        !isEndingSession() && // this tab is already heading to /login itself
        !isPublicPath(window.location.pathname)
      ) {
        window.location.assign("/login");
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  return children;
}