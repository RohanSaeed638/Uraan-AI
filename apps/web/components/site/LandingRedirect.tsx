"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuthStore } from "@/store/auth";

// The landing page is for visitors; someone already signed in goes to their dashboard.
export default function LandingRedirect() {
  const { user, loading } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [loading, user, router]);

  return null;
}
