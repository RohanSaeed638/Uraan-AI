"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";

import { LibraryResource, recommendedResources } from "@/lib/api/resources";

import ResourceCard from "./ResourceCard";

/** Library resources that fit this task, shown on the task page. */
export default function RecommendedResources({ taskId }: { taskId: string }) {
  const t = useTranslations("resources");
  const queryClient = useQueryClient();
  const key = ["resources", "recommended", taskId];

  const query = useQuery({
    queryKey: key,
    queryFn: () => recommendedResources(taskId, 4),
    staleTime: 5 * 60 * 1000,
  });

  const items = query.data ?? [];

  if (query.isLoading || items.length === 0) return null;

  function update(next: LibraryResource) {
    queryClient.setQueryData<LibraryResource[]>(key, (old) =>
      (old ?? []).map((r) => (r.id === next.id ? next : r))
    );
    // Other lists (the library page) should reload their copy of this one.
    queryClient.invalidateQueries({ queryKey: ["resources", "library"] });
  }

  return (
    <section className="rounded-xl border bg-card p-6">
      <h2 className="text-sm font-semibold">{t("recommendedTitle")}</h2>
      <p className="mt-1 text-sm text-muted-foreground">{t("recommendedText")}</p>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {items.map((resource) => (
          <ResourceCard key={resource.id} resource={resource} onChange={update} />
        ))}
      </div>
    </section>
  );
}
