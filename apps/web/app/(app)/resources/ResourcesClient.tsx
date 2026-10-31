"use client";

import { useEffect, useState } from "react";
import PageHeader from "@/components/shared/PageHeader";
import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";

import {
  LibraryResource,
  ResourceFilters,
  ResourceList,
  listResources,
} from "@/lib/api/resources";
import { useCareerOptions } from "@/lib/careers";

import ResourceCard from "@/components/resources/ResourceCard";
import FilterChips from "@/components/shared/FilterChips";
import FilterGroup from "@/components/shared/FilterGroup";
import NativeSelect from "@/components/shared/NativeSelect";
import SearchField from "@/components/shared/SearchField";
import ToggleChip from "@/components/shared/ToggleChip";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const TYPES = ["course", "video", "docs", "book", "practice"] as const;
const LEVELS = ["beginner", "intermediate", "advanced"] as const;

const EMPTY: ResourceFilters = {
  q: "",
  career: "",
  type: "",
  difficulty: "",
  free_only: false,
  bookmarked: false,
  sort: "recommended",
};

export default function ResourcesClient() {
  const t = useTranslations("resources");
  const queryClient = useQueryClient();
  const { options: careers } = useCareerOptions();

  const [filters, setFilters] = useState<ResourceFilters>(EMPTY);

  // Search as the person types, but only ask the API once they pause.
  const [q, setQ] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setQ(filters.q ?? ""), 250);

    return () => clearTimeout(timer);
  }, [filters.q]);

  const applied = { ...filters, q };

  const query = useQuery({
    queryKey: ["resources", "library", applied],
    queryFn: () => listResources(applied),
    placeholderData: keepPreviousData,
  });

  const items = query.data?.items ?? [];
  const set = (patch: Partial<ResourceFilters>) =>
    setFilters((f) => ({ ...f, ...patch }));

  // A bookmark or rating changes one card: update it in place.
  function update(next: LibraryResource) {
    queryClient.setQueryData<ResourceList>(["resources", "library", applied], (old) =>
      old
        ? {
            ...old,
            // Unsaving on the "saved" tab removes the card.
            items: old.items
              .map((r) => (r.id === next.id ? next : r))
              .filter((r) => !(applied.bookmarked && !r.bookmarked)),
          }
        : old
    );
  }

  const filtered =
    !!(q || filters.career || filters.type || filters.difficulty || filters.free_only || filters.bookmarked);

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader title={t("title")} subtitle={t("subtitle")} />

      <Card className="mt-6 gap-5 p-5">
        <SearchField
          label={t("search")}
          placeholder={t("search")}
          value={filters.q ?? ""}
          onChange={(q) => set({ q })}
        />

        <div className="flex flex-wrap items-end gap-x-8 gap-y-4">
          <FilterGroup label={t("filterType")}>
            <FilterChips
              label={t("filterType")}
              size="sm"
              value={filters.type ?? ""}
              onChange={(type) => set({ type })}
              options={[
                { value: "", label: t("all") },
                ...TYPES.map((x) => ({ value: x, label: t(`types.${x}`) })),
              ]}
            />
          </FilterGroup>

          <FilterGroup label={t("filterLevel")}>
            <FilterChips
              label={t("filterLevel")}
              size="sm"
              value={filters.difficulty ?? ""}
              onChange={(difficulty) => set({ difficulty })}
              options={[
                { value: "", label: t("all") },
                ...LEVELS.map((x) => ({ value: x, label: t(`levels.${x}`) })),
              ]}
            />
          </FilterGroup>
        </div>

        <div className="flex flex-wrap items-end gap-x-6 gap-y-3">
          <FilterGroup label={t("filterCareer")} className="w-56">
            <NativeSelect
              aria-label={t("filterCareer")}
              active={!!filters.career}
              value={filters.career}
              onChange={(e) => set({ career: e.target.value })}
            >
              <option value="">{t("anyCareer")}</option>
              {careers.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </NativeSelect>
          </FilterGroup>

          <FilterGroup label={t("sort")} className="w-44">
            <NativeSelect
              aria-label={t("sort")}
              value={filters.sort}
              onChange={(e) => set({ sort: e.target.value as ResourceFilters["sort"] })}
            >
              <option value="recommended">{t("sortBest")}</option>
              <option value="title">{t("sortTitle")}</option>
              <option value="newest">{t("sortNewest")}</option>
            </NativeSelect>
          </FilterGroup>

          <ToggleChip
            checked={!!filters.free_only}
            onChange={(free_only) => set({ free_only })}
          >
            {t("freeOnly")}
          </ToggleChip>

          <ToggleChip
            checked={!!filters.bookmarked}
            onChange={(bookmarked) => set({ bookmarked })}
          >
            {t("savedOnly")}
          </ToggleChip>
        </div>
      </Card>

      <p className="mt-4 text-sm text-muted-foreground" aria-live="polite">
        {query.data ? t("count", { count: query.data.total }) : ""}
      </p>

      {query.isError ? (
        <Card className="mt-3 items-center p-8 text-center text-sm text-muted-foreground">
          {t("loadError")}
        </Card>
      ) : items.length === 0 && !query.isFetching ? (
        <Card className="mt-3 items-center gap-3 p-8 text-center">
          <p className="text-sm text-muted-foreground">
            {filters.bookmarked ? t("noSaved") : t("noResults")}
          </p>
          {filtered && (
            <Button variant="outline" onClick={() => setFilters(EMPTY)}>
              {t("clearFilters")}
            </Button>
          )}
        </Card>
      ) : (
        <div
          className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          aria-busy={query.isFetching}
        >
          {items.map((resource) => (
            <ResourceCard key={resource.id} resource={resource} onChange={update} />
          ))}
        </div>
      )}
    </div>
  );
}
