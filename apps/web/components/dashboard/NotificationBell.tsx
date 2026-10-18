"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell } from "lucide-react";

import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "@/lib/api/notifications";
import { AppNotification } from "@/types/api";
import { cn } from "@/lib/utils";

const KEY = ["notifications"] as const;

function timeAgo(iso: string) {
  const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data } = useQuery({
    queryKey: KEY,
    queryFn: listNotifications,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: KEY });

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
        aria-label={unread ? `Notifications, ${unread} unread` : "Notifications"}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="relative flex size-9 items-center justify-center rounded-full text-muted-foreground transition hover:bg-accent hover:text-accent-foreground"
      >
        <Bell size={17} />
        {unread > 0 && (
          <span className="absolute right-1 top-1 flex min-w-4 items-center justify-center rounded-full bg-brand-gold px-1 text-[10px] font-semibold leading-4 text-black">
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
          <div className="absolute right-0 top-11 z-40 w-80 overflow-hidden rounded-2xl border bg-popover text-popover-foreground shadow-lg">
            <div className="flex items-center justify-between border-b px-4 py-3">
              <p className="text-sm font-semibold">Notifications</p>
              {unread > 0 && (
                <button
                  onClick={() => readAll.mutate()}
                  className="text-xs font-medium text-brand-violet hover:underline"
                >
                  Mark all read
                </button>
              )}
            </div>

            <div className="max-h-96 overflow-y-auto">
              {!data || data.notifications.length === 0 ? (
                <p className="px-4 py-8 text-center text-sm text-muted-foreground">
                  You&apos;re all caught up.
                </p>
              ) : (
                data.notifications.map((n) => (
                  <button
                    key={n.id}
                    onClick={() => open_(n)}
                    className={cn(
                      "block w-full border-b px-4 py-3 text-left transition last:border-b-0 hover:bg-muted",
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
          </div>
        </>
      )}
    </div>
  );
}
