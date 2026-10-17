"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  CheckSquare,
  FolderKanban,
  LayoutGrid,
  Settings,
  Sparkles,
  Target,
  TrendingUp,
  User,
} from "lucide-react";

import Logo from "@/components/shared/Logo";
import { cn } from "@/lib/utils";

const items = [
  { title: "Dashboard", href: "/dashboard", icon: LayoutGrid },
  { title: "My Roadmaps", href: "/roadmaps", icon: Target },
  { title: "Learning", href: "/learning", icon: BookOpen },
  { title: "Tasks", href: "/tasks", icon: CheckSquare },
  { title: "Projects", href: "/projects", icon: FolderKanban },
  { title: "Progress", href: "/progress", icon: TrendingUp },
  { title: "Profile", href: "/profile", icon: User },
  { title: "Settings", href: "/settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sticky top-0 flex h-screen w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar p-5">
      <div className="px-2 py-2">
        <Logo variant="full" size={28} />
      </div>

      <nav className="mt-8 flex flex-col gap-1">
        {items.map((item) => {
          const active =
            pathname === item.href || pathname.startsWith(item.href + "/");

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-2xl px-3.5 py-2.5 text-sm font-medium transition",
                active
                  ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-sm"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              )}
            >
              <item.icon size={18} strokeWidth={2} />
              {item.title}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto rounded-2xl bg-gradient-to-br from-brand-violet to-indigo-900 p-4 text-white">
        <Sparkles size={18} className="text-brand-gold-light" />
        <p className="mt-2 text-sm font-semibold">Upgrade to Pro</p>
        <p className="mt-1 text-xs text-white/70">
          Unlock advanced roadmaps and AI features.
        </p>
      </div>
    </aside>
  );
}
