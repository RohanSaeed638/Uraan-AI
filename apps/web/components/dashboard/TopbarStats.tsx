"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Flame, Zap } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect } from "react";

import { getGamificationMe } from "@/lib/api/gamification";

/** Streak and level, always in view at the top. Quiet while loading, and absent if it cannot be loaded. */
export default function TopbarStats() {
  const t = useTranslations("topbar");
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["gamification", "me"],
    queryFn: getGamificationMe,
    staleTime: 30_000,
    retry: false,
  });

  // Finishing a lesson or task changes both numbers: look again straight away.
  useEffect(() => {
    const refresh = () => queryClient.invalidateQueries({ queryKey: ["gamification", "me"] });

    window.addEventListener("uraan:progress", refresh);

    return () => window.removeEventListener("uraan:progress", refresh);
  }, [queryClient]);

  if (!query.data) return null;

  return (
    <ul className="hidden items-center gap-2 lg:flex" aria-label={t("stats")}>
      <li className="flex items-center gap-1.5 rounded-full bg-brand-gold/15 px-3 py-1 text-xs font-semibold">
        <Flame size={14} className="text-brand-gold" aria-hidden />
        <span className="num">{t("streak", { count: query.data.streak_days })}</span>
      </li>
      <li className="flex items-center gap-1.5 rounded-full bg-brand-violet/15 px-3 py-1 text-xs font-semibold text-violet-700 dark:text-brand-violet-light">
        <Zap size={14} aria-hidden />
        <span className="num">{t("level", { level: query.data.level })}</span>
      </li>
    </ul>
  );
}
