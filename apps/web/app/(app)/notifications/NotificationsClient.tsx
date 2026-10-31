"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import {
  Award,
  Bell,
  CalendarClock,
  CalendarDays,
  CheckCheck,
  Flame,
  LucideIcon,
  Megaphone,
  Trophy,
} from "lucide-react";

import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "@/lib/api/notifications";
import { useTimeAgo } from "@/lib/use-time-ago";
import { cn } from "@/lib/utils";
import { AppNotification } from "@/types/api";

import EmptyState from "@/components/shared/EmptyState";
import FilterChips from "@/components/shared/FilterChips";
import LoadingButton from "@/components/shared/LoadingButton";
import PageHeader from "@/components/shared/PageHeader";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const PAGE = 20;

const ICONS: Record<string, LucideIcon> = {
  daily_reminder: Bell,
  weekly_summary: CalendarDays,
  achievement: Award,
  boss_defeated: Trophy,
  streak: Flame,
  schedule_updated: CalendarClock,
  announcement: Megaphone,
};

type Filter = "all" | "unread";

/** Every notification, newest first: the bell shows only the latest few. */
export default function NotificationsClient() {
  const t = useTranslations("notifications");
  const timeAgo = useTimeAgo();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<Filter>("all");

  const query = useInfiniteQuery({
    queryKey: ["notifications", "list", filter],
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      listNotifications({ limit: PAGE, before: pageParam, unread: filter === "unread" }),
    getNextPageParam: (last) =>
      last.has_more ? last.notifications[last.notifications.length - 1]?.created_at : undefined,
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["notifications"] });
  const readOne = useMutation({ mutationFn: markNotificationRead, onSuccess: refresh });
  const readAll = useMutation({ mutationFn: markAllNotificationsRead, onSuccess: refresh });

  const items = query.data?.pages.flatMap((page) => page.notifications) ?? [];
  const unread = query.data?.pages[0]?.unread_count ?? 0;

  function open(n: AppNotification) {
    if (!n.read) readOne.mutate(n.id);
    if (n.url) router.push(n.url);
  }

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        title={t("pageTitle")}
        subtitle={t("pageSubtitle")}
        actions={
          unread > 0 && (
            <Button variant="outline" className="gap-2" onClick={() => readAll.mutate()}>
              <CheckCheck size={16} /> {t("markAll")}
            </Button>
          )
        }
      />

      <FilterChips
        className="mt-6"
        label={t("filter")}
        value={filter}
        onChange={setFilter}
        options={[
          { value: "all", label: t("all") },
          { value: "unread", label: t("onlyUnread"), count: filter === "unread" ? undefined : unread },
        ]}
      />

      {query.isLoading ? (
        <p className="mt-8 text-center text-sm text-muted-foreground">{t("loading")}</p>
      ) : query.isError ? (
        <EmptyState
          className="mt-6"
          icon={Bell}
          title={t("loadFailed")}
          action={
            <Button variant="outline" onClick={() => query.refetch()}>
              {t("retry")}
            </Button>
          }
        />
      ) : items.length === 0 ? (
        <EmptyState
          className="mt-6"
          icon={Bell}
          title={filter === "unread" ? t("noUnread") : t("none")}
          text={filter === "unread" ? undefined : t("noneText")}
        />
      ) : (
        <>
          <Card className="mt-5 gap-0 p-0">
            {items.map((n) => {
              const Icon = ICONS[n.type] ?? Bell;

              return (
                <button
                  key={n.id}
                  type="button"
                  onClick={() => open(n)}
                  className={cn(
                    "flex w-full items-start gap-4 border-b px-5 py-4 text-start transition last:border-b-0 hover:bg-muted/60",
                    !n.read && "bg-brand-gold/5"
                  )}
                >
                  <span
                    className={cn(
                      "mt-0.5 flex size-10 shrink-0 items-center justify-center rounded-xl",
                      n.read
                        ? "bg-muted text-muted-foreground"
                        : "bg-brand-gold/15 text-brand-gold-deep dark:text-brand-gold"
                    )}
                  >
                    <Icon size={18} />
                  </span>

                  <span className="min-w-0 flex-1">
                    <span className="flex items-start justify-between gap-3">
                      <span className={cn("break-words text-sm", n.read ? "font-medium" : "font-semibold")}>
                        {n.title}
                      </span>
                      <span className="shrink-0 text-xs text-muted-foreground">
                        {timeAgo(n.created_at)}
                      </span>
                    </span>
                    <span className="mt-1 block break-words text-sm text-muted-foreground">{n.body}</span>
                  </span>

                  {!n.read && (
                    <span aria-label={t("unreadDot")} className="mt-2 size-2 shrink-0 rounded-full bg-brand-gold" />
                  )}
                </button>
              );
            })}
          </Card>

          {query.hasNextPage && (
            <div className="mt-5 flex justify-center">
              <LoadingButton
                variant="outline"
                loading={query.isFetchingNextPage}
                onClick={() => query.fetchNextPage()}
              >
                {t("loadMore")}
              </LoadingButton>
            </div>
          )}
        </>
      )}
    </div>
  );
}
