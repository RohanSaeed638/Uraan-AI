"use client";

import { User } from "@supabase/supabase-js";
import { useState } from "react";
import { useTranslations } from "next-intl";
import { Menu, Search, X } from "lucide-react";

import GlobalSearch from "./GlobalSearch";
import { MobileSidebar } from "./Sidebar";
import NotificationBell from "./NotificationBell";
import UserDropdown from "./UserDropdown";

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "morning";
  if (hour < 18) return "afternoon";
  return "evening";
}

export default function Navbar({ user, isAdmin = false }: { user: User; isAdmin?: boolean }) {
  const t = useTranslations("topbar");
  const tNav = useTranslations("nav");
  const tSearch = useTranslations("search");
  const [searchOpen, setSearchOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const firstName: string =
    (user.user_metadata?.full_name as string | undefined)?.split(" ")[0] ??
    t("there");

  return (
    <header className="relative flex h-16 items-center justify-between gap-3 px-4 sm:gap-4 sm:px-8">
      <button
        type="button"
        aria-label={tNav("openMenu")}
        onClick={() => setMenuOpen(true)}
        className="flex size-9 shrink-0 items-center justify-center rounded-full text-muted-foreground transition hover:bg-accent hover:text-accent-foreground lg:hidden"
      >
        <Menu size={20} />
      </button>
      <MobileSidebar open={menuOpen} onClose={() => setMenuOpen(false)} isAdmin={isAdmin} />

      <div className="min-w-0 flex-1 md:flex-none">
        <h2 className="truncate font-heading text-sm font-semibold sm:text-base">
          {t(getGreeting(), { name: `\u2068${firstName}\u2069` })}
        </h2>
        <p className="hidden text-xs text-muted-foreground sm:block">
          {t("encourage")}
        </p>
      </div>

      <div className="hidden max-w-sm flex-1 items-center md:flex">
        <GlobalSearch />
      </div>

      <div className="flex shrink-0 items-center gap-1 sm:gap-3">
        <button
          type="button"
          aria-label={tSearch("open")}
          onClick={() => setSearchOpen(true)}
          className="flex size-9 items-center justify-center rounded-full text-muted-foreground transition hover:bg-accent hover:text-accent-foreground md:hidden"
        >
          <Search size={18} aria-hidden />
        </button>
        <NotificationBell />

        <UserDropdown user={user} />
      </div>

      {searchOpen && (
        <div className="absolute inset-x-0 top-0 z-40 flex h-16 items-center gap-2 border-b border-border bg-background px-4 md:hidden">
          <GlobalSearch autoFocus onDone={() => setSearchOpen(false)} />
          <button
            type="button"
            aria-label={tSearch("close")}
            onClick={() => setSearchOpen(false)}
            className="flex size-9 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:bg-accent"
          >
            <X size={18} aria-hidden />
          </button>
        </div>
      )}
    </header>
  );
}
