"use client";

import { User } from "@supabase/supabase-js";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { LogOut, Settings, User as UserIcon, ChevronDown } from "lucide-react";

import { authService } from "@/services/auth/auth";
import { useAuthStore } from "@/store/auth";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export default function UserDropdown({ user }: { user: User }) {
  const router = useRouter();
  const clearUser = useAuthStore((state) => state.logout);

  const fullName: string = user.user_metadata?.full_name ?? "Student";
  const initials = fullName
    .split(" ")
    .map((n) => n[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  async function logout() {
    // Clear client state immediately rather than waiting on the async
    // onAuthStateChange listener — otherwise there's a window where
    // other pages (e.g. the landing page) can still see a stale user.
    clearUser();
    await authService.logout();
    toast.success("Logged out");
    // A hard navigation (not router.replace/refresh) so the Router
    // Cache and any in-memory component state are fully reset, and the
    // request to /login is guaranteed to reflect the now-cleared
    // session cookies via the proxy's session refresh.
    window.location.href = "/login";
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="flex items-center gap-2.5 rounded-full py-1 pl-1 pr-2.5 transition hover:bg-accent">
        <Avatar>
          <AvatarImage src={user.user_metadata?.avatar_url} />
          <AvatarFallback className="bg-brand-violet text-white">
            {initials}
          </AvatarFallback>
        </Avatar>
        <span className="hidden text-left leading-tight sm:block">
          <span className="block text-sm font-medium">{fullName}</span>
          <span className="block text-xs text-muted-foreground">Student</span>
        </span>
        <ChevronDown size={14} className="hidden text-muted-foreground sm:block" />
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>
          <span className="block text-sm font-medium">{fullName}</span>
          <span className="block text-xs font-normal text-muted-foreground">
            {user.email}
          </span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => router.push("/profile")}>
          <UserIcon size={16} /> Profile
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => router.push("/settings")}>
          <Settings size={16} /> Settings
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={logout}
          className="text-destructive focus:text-destructive"
        >
          <LogOut size={16} /> Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
