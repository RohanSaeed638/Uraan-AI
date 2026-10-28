"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell } from "lucide-react";
import { toast } from "sonner";

import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "@/lib/api/notifications";
import { fireConfetti } from "@/components/shared/ConfettiHost";
import { AppNotification } from "@/types/api";
import { useTimeAgo } from "@/lib/use-time-ago";
import { cn } from "@/lib/utils";

const KEY = ["notifications"] as const;

// Notifications that deserve a celebration when they arrive.
const CELEBRATE = new Set(["achievement", "boss_defeated"]);

export default function NotificationBell() {
  const t = useTranslations("notifications");
  const timeAgo = useTimeAgo();
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data } = useQuery({
    queryKey: KEY,
    queryFn: () => listNotifications(),
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: KEY });

  // What was already there when the page loaded is not news; only what shows
  // up afterwards is celebrated.
  const seen = useRef<Set<string> | null>(null);

  useEffect(() => {
    if (!data) return;

    if (seen.current === null) {
      seen.current = new Set(data.notifications.map((n) => n.id));
      return;
    }

    const fresh = data.notifications.filter(
      (n) => !seen.current!.has(n.id) && CELEBRATE.has(n.type)
    );

    data.notifications.forEach((n) => seen.current!.add(n.id));

    if (fresh.length > 0) {
      fireConfetti();
      fresh.slice(0, 3).forEach((n) => toast.success(n.title, { description: n.body }));
    }
  }, [data]);

  // Check for new notifications soon after anything that can earn one.
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;

    function soon() {
      clearTimeout(timer);
      timer = setTimeout(() => queryClient.invalidateQueries({ queryKey: KEY }), 700);
    }

    window.addEventListener("uraan:progress", soon);

    return () => {
      clearTimeout(timer);
      window.removeEventListener("uraan:progress", soon);
    };
  }, [queryClient]);

  const readOne = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: refresh,
  });
  const readAll = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: refresh,
  });

  const unread = data?.unread_count ?? 0;

  function open_(n: AppNotification) {
    if (!n.read) readOne.mutate(n.id);
    setOpen(false);
    if (n.url) router.push(n.url);
  }

  return (
    <div className="relative">
      <button
        aria-label={unread ? t("unread", { count: unread }) : t("title")}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="relative flex size-9 items-center justify-center rounded-full text-muted-foreground transition hover:bg-accent hover:text-accent-foreground"
      >
        <Bell size={17} />
        {unread > 0 && (
          <span className="absolute end-1 top-1 flex min-w-4 items-center justify-center rounded-full bg-brand-gold px-1 text-[10px] font-semibold leading-4 text-black">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <>
          <div
            className="fixed inset-0 z-30"
            onClick={() => setOpen(false)}
            aria-hidden
          />
          <div className="absolute end-0 top-11 z-40 w-80 overflow-hidden rounded-2xl border bg-popover text-popover-foreground shadow-lg">
            <div className="flex items-center justify-between border-b px-4 py-3">
              <p className="text-sm font-semibold">{t("title")}</p>
              {unread > 0 && (
                <button
                  onClick={() => readAll.mutate()}
                  className="text-xs font-medium text-brand-gold-deep dark:text-brand-gold hover:underline"
                >
                  {t("markAll")}
                </button>
              )}
            </div>

            <div className="max-h-96 overflow-y-auto">
              {!data || data.notifications.length === 0 ? (
                <p className="px-4 py-8 text-center text-sm text-muted-foreground">
                  {t("caughtUp")}
                </p>
              ) : (
                data.notifications.map((n) => (
                  <button
                    key={n.id}
                    onClick={() => open_(n)}
                    className={cn(
                      "block w-full border-b px-4 py-3 text-start transition last:border-b-0 hover:bg-muted",
                      !n.read && "bg-brand-violet/5"
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm font-medium">{n.title}</p>
                      <span className="shrink-0 text-[11px] text-muted-foreground">
                        {timeAgo(n.created_at)}
                      </span>
                    </div>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {n.body}
                    </p>
                  </button>
                ))
              )}
            </div>

            <Link
              href="/notifications"
              onClick={() => setOpen(false)}
              className="block border-t px-4 py-2.5 text-center text-xs font-medium text-brand-gold-deep hover:bg-muted dark:text-brand-gold"
            >
              {t("viewAll")}
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
