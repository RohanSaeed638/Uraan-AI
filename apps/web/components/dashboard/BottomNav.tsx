"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import { Bot, CalendarDays, LayoutGrid, Target, TrendingUp } from "lucide-react";

import { cn } from "@/lib/utils";

const items = [
  { key: "dashboard", href: "/dashboard", icon: LayoutGrid },
  { key: "roadmaps", href: "/roadmaps", icon: Target },
  { key: "calendar", href: "/calendar", icon: CalendarDays },
  { key: "mentor", href: "/mentor", icon: Bot },
  { key: "progress", href: "/progress", icon: TrendingUp },
] as const;

// The five places used every day, one thumb away on a phone. The sidebar
// (opened from the menu button) still has everything else.
export default function BottomNav() {
  const pathname = usePathname();
  const t = useTranslations("nav");

  return (
    <nav
      aria-label={t("quick")}
      className="z-20 flex border-t border-border bg-background pb-[env(safe-area-inset-bottom)] lg:hidden print:hidden"
    >
      {items.map(({ key, href, icon: Icon }) => {
        const active = pathname === href || pathname.startsWith(`${href}/`);

        return (
          <Link
            key={key}
            href={href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex min-h-14 flex-1 flex-col items-center justify-center gap-0.5 px-1 text-[11px] font-medium",
              active ? "text-violet-700 dark:text-brand-violet-light" : "text-muted-foreground"
            )}
          >
            <Icon className="size-5" aria-hidden />
            <span className="max-w-full truncate">{t(key)}</span>
          </Link>
        );
      })}
    </nav>
  );
}
