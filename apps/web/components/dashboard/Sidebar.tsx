"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import {
  Bot,
  BookOpen,
  Briefcase,
  CalendarDays,
  CheckSquare,
  FileText,
  FolderKanban,
  LayoutGrid,
  Mic,
  Settings,
  Sparkles,
  Target,
  TrendingUp,
  Trophy,
  User,
  X,
} from "lucide-react";

import Logo from "@/components/shared/Logo";
import { cn } from "@/lib/utils";

const items = [
  { title: "Dashboard", href: "/dashboard", icon: LayoutGrid },
  { title: "My Roadmaps", href: "/roadmaps", icon: Target },
  { title: "Learning", href: "/learning", icon: BookOpen },
  { title: "Calendar", href: "/calendar", icon: CalendarDays },
  { title: "Tasks", href: "/tasks", icon: CheckSquare },
  { title: "Projects", href: "/projects", icon: FolderKanban },
  { title: "Progress", href: "/progress", icon: TrendingUp },
  { title: "Resume", href: "/resume", icon: FileText },
  { title: "Portfolio", href: "/portfolio", icon: Briefcase },
  { title: "Interview", href: "/interview", icon: Mic },
  { title: "AI Mentor", href: "/mentor", icon: Bot },
  { title: "Leaderboard", href: "/leaderboard", icon: Trophy },
  { title: "Profile", href: "/profile", icon: User },
  { title: "Settings", href: "/settings", icon: Settings },
];

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <>
      <div className="shrink-0 px-2 py-2">
        <Logo variant="full" size={28} />
      </div>

      {/* Scrolls on short screens so the upgrade card never overlaps it. */}
      <nav className="mt-6 flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto">
        {items.map((item) => {
          const active =
            pathname === item.href || pathname.startsWith(item.href + "/");

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-2xl px-3.5 py-2.5 text-sm font-medium transition",
                active
                  ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-sm"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              )}
            >
              <item.icon size={18} strokeWidth={2} className="shrink-0" />
              {item.title}
            </Link>
          );
        })}
      </nav>

      <div className="mt-4 shrink-0 rounded-2xl bg-gradient-to-br from-brand-violet to-indigo-900 p-4 text-white">
        <Sparkles size={18} className="text-brand-gold-light" />
        <p className="mt-2 text-sm font-semibold">Upgrade to Pro</p>
        <p className="mt-1 text-xs text-white/70">
          Unlock advanced roadmaps and AI features.
        </p>
      </div>
    </>
  );
}

/** Fixed sidebar on large screens. */
export default function Sidebar() {
  return (
    <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar p-5 lg:flex print:hidden">
      <SidebarContent />
    </aside>
  );
}

/** Slide-over menu for screens narrower than `lg`. */
export function MobileSidebar({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  useEffect(() => {
    if (!open) return;

    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 lg:hidden print:hidden"
      role="dialog"
      aria-modal="true"
      aria-label="Navigation"
    >
      <button
        type="button"
        aria-label="Close menu"
        className="absolute inset-0 bg-black/60"
        onClick={onClose}
      />
      <aside className="relative flex h-full w-72 max-w-[85vw] flex-col border-r border-sidebar-border bg-sidebar p-5 shadow-xl">
        <button
          type="button"
          aria-label="Close menu"
          onClick={onClose}
          className="absolute right-3 top-3 rounded-full p-2 text-sidebar-foreground/70 transition hover:bg-sidebar-accent"
        >
          <X size={18} />
        </button>
        <SidebarContent onNavigate={onClose} />
      </aside>
    </div>
  );
}
