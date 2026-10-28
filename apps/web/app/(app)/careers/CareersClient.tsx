"use client";

import { useEffect, useState } from "react";
import PageHeader from "@/components/shared/PageHeader";
import Link from "next/link";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { Scale, Sparkles } from "lucide-react";

import { listCareers } from "@/lib/api/careers";
import { CareerFilters, CareerList } from "@/types/api";

import FilterChips from "@/components/shared/FilterChips";
import FilterGroup from "@/components/shared/FilterGroup";
import NativeSelect from "@/components/shared/NativeSelect";
import SearchField from "@/components/shared/SearchField";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

import CareerCard from "./CareerCard";
import RecommendDialog from "./RecommendDialog";

const MAX_COMPARE = 4;

const SALARY_STEPS = [0, 50000, 100000, 200000, 400000];

export default function CareersClient({ initial }: { initial: CareerList | null }) {
  const t = useTranslations("careers");

  const [filters, setFilters] = useState<CareerFilters>({
    search: "",
    difficulty: "",
    demand: "",
    min_salary: 0,
  });
  const [picked, setPicked] = useState<string[]>([]);
  const [helpOpen, setHelpOpen] = useState(false);

  // Search as the person types, but only ask the API once they pause.
  const [search, setSearch] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setSearch(filters.search ?? ""), 250);

    return () => clearTimeout(timer);
  }, [filters.search]);

  const applied: CareerFilters = { ...filters, search };

  const pristine =
    !applied.search && !applied.difficulty && !applied.demand && !applied.min_salary;

  const query = useQuery({
    queryKey: ["careers", applied],
    queryFn: () => listCareers(applied),
    placeholderData: keepPreviousData,
    initialData: pristine && initial ? initial : undefined,
  });

  const items = query.data?.items ?? [];

  const toggle = (slug: string) =>
    setPicked((prev) =>
      prev.includes(slug)
        ? prev.filter((s) => s !== slug)
        : prev.length < MAX_COMPARE
          ? [...prev, slug]
          : prev
    );

  const set = (patch: Partial<CareerFilters>) =>
    setFilters((f) => ({ ...f, ...patch }));

  return (
    <main className="mx-auto max-w-6xl pb-24">
      <PageHeader
        title={t("title")}
        subtitle={t("subtitle")}
        actions={
          <Button onClick={() => setHelpOpen(true)} className="gap-2">
            <Sparkles size={16} />
            {t("helpMeChoose")}
          </Button>
        }
      />

      <Card className="mb-6 gap-5 p-5">
        <SearchField
          label={t("search")}
          placeholder={t("search")}
          value={filters.search ?? ""}
          onChange={(search) => set({ search })}
        />

        <div className="flex flex-wrap items-end gap-x-8 gap-y-4">
          <FilterGroup label={t("filterDifficulty")}>
            <FilterChips
              label={t("filterDifficulty")}
              size="sm"
              value={filters.difficulty ?? ""}
              onChange={(difficulty) => set({ difficulty })}
              options={[
                { value: "", label: t("all") },
                ...(["beginner", "intermediate", "advanced"] as const).map((d) => ({
                  value: d,
                  label: t(`difficulty.${d}`),
                })),
              ]}
            />
          </FilterGroup>

          <FilterGroup label={t("filterDemand")}>
            <FilterChips
              label={t("filterDemand")}
              size="sm"
              value={filters.demand ?? ""}
              onChange={(demand) => set({ demand })}
              options={[
                { value: "", label: t("all") },
                ...(["medium", "high", "very_high"] as const).map((d) => ({
                  value: d,
                  label: t(`demand.${d}`),
                })),
              ]}
            />
          </FilterGroup>

          <FilterGroup label={t("filterSalary")} className="w-48">
            <NativeSelect
              aria-label={t("filterSalary")}
              active={!!filters.min_salary}
              value={filters.min_salary}
              onChange={(e) => set({ min_salary: Number(e.target.value) })}
            >
              {SALARY_STEPS.map((n) => (
                <option key={n} value={n}>
                  {n === 0
                    ? t("anySalary")
                    : t("salaryFrom", { amount: `PKR ${n / 1000}k` })}
                </option>
              ))}
            </NativeSelect>
          </FilterGroup>
        </div>
      </Card>

      {query.isError ? (
        <Card className="items-center p-8 text-center text-sm text-muted-foreground">
          {t("loadError")}
        </Card>
      ) : items.length === 0 && !query.isFetching ? (
        <Card className="items-center gap-3 p-8 text-center">
          <p className="text-sm text-muted-foreground">{t("noResults")}</p>
          <Button
            variant="outline"
            onClick={() =>
              setFilters({ search: "", difficulty: "", demand: "", min_salary: 0 })
            }
          >
            {t("clearFilters")}
          </Button>
        </Card>
      ) : (
        <div
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          aria-busy={query.isFetching}
        >
          {items.map((career) => (
            <CareerCard
              key={career.id}
              career={career}
              selected={picked.includes(career.slug)}
              canSelect={picked.length < MAX_COMPARE}
              onToggle={() => toggle(career.slug)}
            />
          ))}
        </div>
      )}

      {picked.length > 0 && (
        <div className="fixed inset-x-0 bottom-0 z-30 px-4 pb-4 lg:start-64">
          <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-between gap-3 rounded-3xl border bg-card p-3 ps-5 shadow-lg">
            <p className="text-sm">
              {t("selected", { count: picked.length, max: MAX_COMPARE })}
            </p>

            <div className="flex gap-2">
              <Button variant="ghost" size="sm" onClick={() => setPicked([])}>
                {t("clear")}
              </Button>

              {picked.length >= 2 ? (
                <Link
                  href={`/careers/compare?slugs=${picked.join(",")}`}
                  className={buttonVariants({ size: "sm", className: "gap-2" })}
                >
                  <Scale size={14} />
                  {t("compareNow")}
                </Link>
              ) : (
                <Button size="sm" disabled className="gap-2">
                  <Scale size={14} />
                  {t("pickOneMore")}
                </Button>
              )}
            </div>
          </div>
        </div>
      )}

      <RecommendDialog open={helpOpen} onOpenChange={setHelpOpen} />
    </main>
  );
}
