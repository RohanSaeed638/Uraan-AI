"use client";

import { useState } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { ScrollText } from "lucide-react";

import { listAudit } from "@/lib/api/admin";

import EmptyState from "@/components/shared/EmptyState";
import FilterChips from "@/components/shared/FilterChips";
import LoadingButton from "@/components/shared/LoadingButton";
import { Card } from "@/components/ui/card";

const PAGE = 30;
const GROUPS = ["all", "career", "resource", "announcement", "user"] as const;

const show = (value: unknown) =>
  value === null || value === undefined ? "–" : typeof value === "string" ? value : JSON.stringify(value);

export default function AdminAuditPage() {
  const t = useTranslations("admin.audit");
  const [group, setGroup] = useState<(typeof GROUPS)[number]>("all");

  const query = useInfiniteQuery({
    queryKey: ["admin", "audit", group],
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      listAudit({ limit: PAGE, before: pageParam, action: group === "all" ? undefined : group }),
    getNextPageParam: (last) => (last.has_more ? last.items[last.items.length - 1]?.at : undefined),
  });

  const items = query.data?.pages.flatMap((p) => p.items) ?? [];

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">{t("intro")}</p>

      <FilterChips
        label={t("filter")}
        size="sm"
        value={group}
        onChange={setGroup}
        options={GROUPS.map((g) => ({ value: g, label: t(`groups.${g}`) }))}
      />

      {query.isError ? (
        <EmptyState icon={ScrollText} title={t("failed")} />
      ) : items.length === 0 && !query.isLoading ? (
        <EmptyState icon={ScrollText} title={t("none")} />
      ) : (
        <Card className="gap-0 p-0">
          {items.map((entry) => (
            <div key={entry.id} className="space-y-1 border-b px-4 py-3 text-sm last:border-0">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <p className="break-words font-medium">{entry.summary}</p>
                <span className="shrink-0 text-xs text-muted-foreground">
                  {entry.at.slice(0, 19).replace("T", " ")} UTC
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                {entry.actor} · {entry.action}
              </p>
              {entry.changes && (
                <ul className="mt-1 space-y-0.5 text-xs">
                  {Object.entries(entry.changes).map(([field, [before, after]]) => (
                    <li key={field} className="break-words">
                      <span className="font-medium">{field}</span>:{" "}
                      <span className="text-muted-foreground line-through">{show(before)}</span>
                      {" → "}
                      <span>{show(after)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </Card>
      )}

      {query.hasNextPage && (
        <div className="flex justify-center">
          <LoadingButton variant="outline" loading={query.isFetchingNextPage} onClick={() => query.fetchNextPage()}>
            {t("older")}
          </LoadingButton>
        </div>
      )}
    </div>
  );
}
