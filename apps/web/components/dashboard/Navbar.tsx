"use client";

import { User } from "@supabase/supabase-js";

import UserDropdown from "./UserDropdown";

export default function Navbar({
  user,
}: {
  user: User;
}) {
  return (
    <header className="h-16 border-b px-8 flex items-center justify-between">
      <div>
        <h2 className="font-semibold">
          Welcome back 👋
        </h2>
      </div>

      <UserDropdown user={user} />
    </header>
  );
}