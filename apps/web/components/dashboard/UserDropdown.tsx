"use client";

import { User } from "@supabase/supabase-js";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { LogOut, Settings, User as UserIcon, ChevronDown } from "lucide-react";

import { authService } from "@/services/auth/auth";
import { useAuthStore } from "@/store/auth";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export default function UserDropdown({ user }: { user: User }) {
  const router = useRouter();
  const t = useTranslations("topbar");
  const tNav = useTranslations("nav");
  const clearUser = useAuthStore((state) => state.logout);

  const fullName: string = user.user_metadata?.full_name ?? t("student");
  const initials = fullName
    .split(" ")
    .map((n) => n[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  async function logout() {
    // Clear client state immediately rather than waiting on the async
    // onAuthStateChange listener, so no page can still see a stale user.
    clearUser();

    try {
      await authService.logout();
    } finally {
      // A hard navigation (not router.replace/refresh) so the Router Cache
      // and all in-memory state are reset, and the request to /login sees
      // the cleared cookies. Runs even if sign-out reported a problem.
      window.location.href = "/login";
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="flex items-center gap-2.5 rounded-full py-1 ps-1 pe-2.5 transition hover:bg-accent">
        <Avatar>
          <AvatarImage src={user.user_metadata?.avatar_url} />
          <AvatarFallback className="bg-brand-violet text-white">
            {initials}
          </AvatarFallback>
        </Avatar>
        <span className="hidden min-w-0 max-w-40 text-start leading-tight sm:block">
          <span className="block truncate text-sm font-medium">{fullName}</span>
          <span className="block text-xs text-muted-foreground">{t("student")}</span>
        </span>
        <ChevronDown size={14} className="hidden text-muted-foreground sm:block" />
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-56">
        {/* A menu label must sit inside a group, or the menu throws on open. */}
        <DropdownMenuGroup>
          <DropdownMenuLabel>
            <span className="block truncate text-sm font-medium">{fullName}</span>
            <span className="block truncate text-xs font-normal text-muted-foreground">
              {user.email}
            </span>
          </DropdownMenuLabel>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => router.push("/profile")}>
          <UserIcon size={16} /> {tNav("profile")}
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => router.push("/settings")}>
          <Settings size={16} /> {tNav("settings")}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={logout}
          className="text-destructive focus:text-destructive"
        >
          <LogOut size={16} /> {t("logout")}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
