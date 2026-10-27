"use client";

import { User } from "@supabase/supabase-js";
import { useState } from "react";
import { useTranslations } from "next-intl";
import { Menu, Search } from "lucide-react";

import { MobileSidebar } from "./Sidebar";
import NotificationBell from "./NotificationBell";
import UserDropdown from "./UserDropdown";

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "morning";
  if (hour < 18) return "afternoon";
  return "evening";
}

export default function Navbar({ user }: { user: User }) {
  const t = useTranslations("topbar");
  const tNav = useTranslations("nav");
  const [menuOpen, setMenuOpen] = useState(false);

  const firstName: string =
    (user.user_metadata?.full_name as string | undefined)?.split(" ")[0] ??
    t("there");

  return (
    <header className="flex h-16 items-center justify-between gap-3 px-4 sm:gap-4 sm:px-8">
      <button
        type="button"
        aria-label={tNav("openMenu")}
        onClick={() => setMenuOpen(true)}
        className="flex size-9 shrink-0 items-center justify-center rounded-full text-muted-foreground transition hover:bg-accent hover:text-accent-foreground lg:hidden"
      >
        <Menu size={20} />
      </button>
      <MobileSidebar open={menuOpen} onClose={() => setMenuOpen(false)} />

      <div className="min-w-0 flex-1 md:flex-none">
        <h2 className="truncate font-heading text-sm font-semibold sm:text-base">
          {t(getGreeting(), { name: `\u2068${firstName}\u2069` })}
        </h2>
        <p className="hidden text-xs text-muted-foreground sm:block">
          {t("encourage")}
        </p>
      </div>

      <div className="hidden max-w-sm flex-1 items-center md:flex">
        <div className="relative w-full">
          <Search
            className="pointer-events-none absolute start-3.5 top-1/2 -translate-y-1/2 text-muted-foreground"
            size={15}
          />
          <input
            type="search"
            placeholder={t("search")}
            className="h-9 w-full rounded-full border border-transparent bg-muted/60 ps-9 pe-3 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30"
          />
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-1 sm:gap-3">
        <NotificationBell />

        <UserDropdown user={user} />
      </div>
    </header>
  );
}
