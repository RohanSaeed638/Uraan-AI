"use client";

import { User } from "@supabase/supabase-js";
import { Search, Bell } from "lucide-react";

import UserDropdown from "./UserDropdown";

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export default function Navbar({ user }: { user: User }) {
  const firstName: string =
    (user.user_metadata?.full_name as string | undefined)?.split(" ")[0] ??
    "there";

  return (
    <header className="flex h-16 items-center justify-between gap-4 px-6 sm:px-8">
      <div>
        <h2 className="font-heading text-sm font-semibold sm:text-base">
          {getGreeting()}, {firstName}! 👋
        </h2>
        <p className="hidden text-xs text-muted-foreground sm:block">
          Keep going! You&apos;re making great progress.
        </p>
      </div>

      <div className="hidden max-w-sm flex-1 items-center sm:flex">
        <div className="relative w-full">
          <Search
            className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground"
            size={15}
          />
          <input
            type="search"
            placeholder="Search anything..."
            className="h-9 w-full rounded-full border border-transparent bg-muted/60 pl-9 pr-3 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30"
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          aria-label="Notifications"
          className="relative flex size-9 items-center justify-center rounded-full text-muted-foreground transition hover:bg-accent hover:text-accent-foreground"
        >
          <Bell size={17} />
          <span className="absolute right-2 top-2 size-1.5 rounded-full bg-brand-gold" />
        </button>

        <UserDropdown user={user} />
      </div>
    </header>
  );
}
