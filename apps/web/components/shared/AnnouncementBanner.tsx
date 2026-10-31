"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { Info, TriangleAlert, X } from "lucide-react";

import { getActiveAnnouncements } from "@/lib/api/admin";
import { cn } from "@/lib/utils";

const KEY = "uraan-dismissed-announcements";

function dismissedIds(): string[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? "[]");
  } catch {
    return [];
  }
}

/** What staff announced to everyone: a strip under the top bar. Each one can be
 * closed; closing is remembered on this device only. */
export default function AnnouncementBanner() {
  const t = useTranslations("announcements");
  const [closed, setClosed] = useState<string[]>([]);

  const { data } = useQuery({
    queryKey: ["announcements", "active"],
    queryFn: getActiveAnnouncements,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  const hidden = new Set([...closed, ...(typeof window === "undefined" ? [] : dismissedIds())]);
  const shown = (data ?? []).filter((a) => !hidden.has(a.id));

  if (shown.length === 0) return null;

  function dismiss(id: string) {
    setClosed((prev) => [...prev, id]);

    try {
      localStorage.setItem(KEY, JSON.stringify([...dismissedIds(), id].slice(-30)));
    } catch {
      // Private mode: it comes back next visit.
    }
  }

  return (
    <div className="space-y-2 px-4 pt-3 sm:px-6 lg:px-8 print:hidden" aria-label={t("label")}>
      {shown.map((a) => {
        const warning = a.level === "warning";
        const Icon = warning ? TriangleAlert : Info;

        return (
          <div
            key={a.id}
            role="status"
            className={cn(
              "flex items-start gap-3 rounded-2xl border px-4 py-3 text-sm",
              warning
                ? "border-amber-500/40 bg-amber-500/10"
                : "border-brand-gold/40 bg-brand-gold/10"
            )}
          >
            <Icon
              size={16}
              className={cn("mt-0.5 shrink-0", warning ? "text-amber-500" : "text-brand-gold")}
            />
            <p className="min-w-0 flex-1 break-words">
              <span className="font-semibold">{a.title}</span>
              <span className="text-muted-foreground"> · {a.body}</span>
            </p>
            <button
              type="button"
              aria-label={t("dismiss")}
              onClick={() => dismiss(a.id)}
              className="shrink-0 rounded-full p-1 text-muted-foreground hover:bg-muted"
            >
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
