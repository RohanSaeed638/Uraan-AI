"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { useTranslations } from "next-intl";
import {
  Bot,
  BookOpen,
  Briefcase,
  CalendarDays,
  CheckSquare,
  Compass,
  Library,
  Medal,
  FileText,
  FolderKanban,
  LayoutGrid,
  Mic,
  Settings,
  ShieldCheck,
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
  { key: "dashboard", href: "/dashboard", icon: LayoutGrid },
  { key: "careers", href: "/careers", icon: Compass },
  { key: "roadmaps", href: "/roadmaps", icon: Target },
  { key: "resources", href: "/resources", icon: Library },
  { key: "learning", href: "/learning", icon: BookOpen },
  { key: "calendar", href: "/calendar", icon: CalendarDays },
  { key: "tasks", href: "/tasks", icon: CheckSquare },
  { key: "projects", href: "/projects", icon: FolderKanban },
  { key: "progress", href: "/progress", icon: TrendingUp },
  { key: "resume", href: "/resume", icon: FileText },
  { key: "portfolio", href: "/portfolio", icon: Briefcase },
  { key: "interview", href: "/interview", icon: Mic },
  { key: "mentor", href: "/mentor", icon: Bot },
  { key: "achievements", href: "/achievements", icon: Medal },
  { key: "leaderboard", href: "/leaderboard", icon: Trophy },
  { key: "profile", href: "/profile", icon: User },
  { key: "settings", href: "/settings", icon: Settings },
];

const adminItem = { key: "admin", href: "/admin", icon: ShieldCheck } as const;

function SidebarContent({ onNavigate, isAdmin }: { onNavigate?: () => void; isAdmin?: boolean }) {
  const pathname = usePathname();
  const t = useTranslations("nav");

  return (
    <>
      <div className="shrink-0 px-2 py-2">
        <Logo variant="full" size={28} />
      </div>

      {/* Scrolls on short screens so the upgrade card never overlaps it. */}
      <nav className="mt-6 flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto">
        {(isAdmin ? [...items, adminItem] : items).map((item) => {
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
              {t(item.key)}
            </Link>
          );
        })}
      </nav>

      <div className="mt-4 shrink-0 rounded-2xl bg-gradient-to-br from-brand-violet to-indigo-900 p-4 text-white">
        <Sparkles size={18} className="text-brand-gold-light" />
        <p className="mt-2 text-sm font-semibold">{t("upgradeTitle")}</p>
        <p className="mt-1 text-xs text-white/70">{t("upgradeText")}</p>
      </div>
    </>
  );
}

/** Fixed sidebar on large screens. */
export default function Sidebar({ isAdmin = false }: { isAdmin?: boolean }) {
  return (
    <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-e border-sidebar-border bg-sidebar p-5 lg:flex print:hidden">
      <SidebarContent isAdmin={isAdmin} />
    </aside>
  );
}

/** Slide-over menu for screens narrower than `lg`. */
export function MobileSidebar({
  open,
  onClose,
  isAdmin = false,
}: {
  open: boolean;
  onClose: () => void;
  isAdmin?: boolean;
}) {
  const t = useTranslations("nav");

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
      aria-label={t("menu")}
    >
      <button
        type="button"
        aria-label={t("closeMenu")}
        className="absolute inset-0 bg-black/60"
        onClick={onClose}
      />
      <aside className="relative flex h-full w-72 max-w-[85vw] flex-col border-e border-sidebar-border bg-sidebar p-5 shadow-xl">
        <button
          type="button"
          aria-label={t("closeMenu")}
          onClick={onClose}
          className="absolute end-3 top-3 rounded-full p-2 text-sidebar-foreground/70 transition hover:bg-sidebar-accent"
        >
          <X size={18} />
        </button>
        <SidebarContent onNavigate={onClose} isAdmin={isAdmin} />
      </aside>
    </div>
  );
}
