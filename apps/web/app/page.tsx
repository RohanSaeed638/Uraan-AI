"use client";

import { useAuthStore } from "@/store/auth";

export default function HomePage() {
  const { user, loading } = useAuthStore();

  if (loading) {
    return <h1>Loading...</h1>;
  }

  return (
    <main className="min-h-screen flex items-center justify-center">
      {user ? (
        <h1>Welcome {user.email}</h1>
      ) : (
        <h1>Not Logged In</h1>
      )}
    </main>
  );
}