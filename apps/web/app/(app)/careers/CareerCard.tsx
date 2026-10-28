"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { Clock, Wallet } from "lucide-react";

import { careerIcon, salaryRange } from "@/lib/careers";
import { careerText } from "@/lib/career-text";
import { cn } from "@/lib/utils";
import { CareerSummary } from "@/types/api";

import Pill from "@/components/shared/Pill";
import { Card } from "@/components/ui/card";

interface Props {
  career: CareerSummary;
  selected: boolean;
  canSelect: boolean;
  onToggle: () => void;
}

export default function CareerCard({
  career,
  selected,
  canSelect,
  onToggle,
}: Props) {
  const t = useTranslations("careers");
  const ct = careerText(useTranslations("catalog"));
  const salary = salaryRange(career.salary_min_pkr, career.salary_max_pkr);

  return (
    <Card
      className={cn(
        "card-lift relative h-full gap-3 p-5",
        selected && "ring-2 ring-brand-violet/60"
      )}
    >
      <div className="flex items-start gap-3">
        <div
          className="flex size-11 shrink-0 items-center justify-center rounded-2xl text-white"
          style={{ backgroundColor: career.color ?? "var(--brand-violet)" }}
        >
          {careerIcon(career.icon, 22)}
        </div>

        <div className="min-w-0 flex-1">
          <Link
            href={`/careers/${career.slug}`}
            className="line-clamp-2 font-heading font-semibold leading-snug hover:underline"
          >
            {ct.name(career.slug, career.name)}
          </Link>
          {career.category && (
            <p className="truncate text-xs text-muted-foreground">
              {ct.category(career.category)}
            </p>
          )}
        </div>
      </div>

      <p className="line-clamp-3 text-sm text-muted-foreground">
        {ct.description(career.slug, career.description)}
      </p>

      <div className="flex flex-wrap gap-2">
        {career.difficulty && (
          <Pill>{t(`difficulty.${career.difficulty}`)}</Pill>
        )}
        {career.market_demand && (
          <Pill tone="soft">
            {t("demandLabel", { level: t(`demand.${career.market_demand}`) })}
          </Pill>
        )}
      </div>

      <div className="mt-auto space-y-1.5 pt-1 text-sm">
        {career.estimated_months && (
          <p className="flex items-center gap-2 text-muted-foreground">
            <Clock size={14} className="shrink-0" />
            {t("months", { count: career.estimated_months })}
          </p>
        )}
        {salary && (
          <p className="flex items-center gap-2 text-muted-foreground">
            <Wallet size={14} className="shrink-0" />
            <span className="truncate">{t("perMonth", { amount: salary })}</span>
          </p>
        )}
      </div>

      <label
        className={cn(
          "mt-1 flex items-center gap-2 text-sm",
          !selected && !canSelect && "opacity-50"
        )}
      >
        <input
          type="checkbox"
          className="size-4 accent-gold"
          checked={selected}
          disabled={!selected && !canSelect}
          onChange={onToggle}
        />
        {t("compare")}
      </label>
    </Card>
  );
}
