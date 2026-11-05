import Link from "next/link";
import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";
import { ArrowLeft, Clock, ExternalLink, Sparkles, Wallet } from "lucide-react";

import { careerIcon, salaryRange } from "@/lib/careers";
import { careerText } from "@/lib/career-text";
import { getCareerDetailServer } from "@/lib/server/data";

import Pill from "@/components/shared/Pill";
import { buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default async function CareerDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const career = await getCareerDetailServer(slug);

  if (!career) notFound();

  const t = await getTranslations("careers");
  const ct = careerText(await getTranslations("catalog"));
  const salary = salaryRange(career.salary_min_pkr, career.salary_max_pkr);

  return (
    <div className="mx-auto max-w-4xl">
      <Link
        href="/careers"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft size={14} className="rtl:rotate-180" /> {t("backToCareers")}
      </Link>

      <Card className="gap-5 p-6">
        <div className="flex flex-wrap items-start gap-4">
          <div
            className="flex size-14 shrink-0 items-center justify-center rounded-2xl text-white"
            style={{ backgroundColor: career.color ?? "var(--brand-violet)" }}
          >
            {careerIcon(career.icon, 28)}
          </div>

          <div className="min-w-0 flex-1">
            <h1 className="font-heading text-2xl font-bold sm:text-3xl">
              {ct.name(career.slug, career.name)}
            </h1>
            <div className="mt-2 flex flex-wrap gap-2">
              {career.category && <Pill>{ct.category(career.category)}</Pill>}
              {career.difficulty && (
                <Pill>{t(`difficulty.${career.difficulty}`)}</Pill>
              )}
              {career.market_demand && (
                <Pill tone="soft">
                  {t("demandLabel", { level: t(`demand.${career.market_demand}`) })}
                </Pill>
              )}
            </div>
          </div>

          <Link
            href={`/roadmaps?career=${career.slug}`}
            className={buttonVariants({ className: "gap-2" })}
          >
            <Sparkles size={16} />
            {t("generateRoadmap")}
          </Link>
        </div>

        <p className="text-muted-foreground">{ct.description(career.slug, career.description)}</p>

        <div className="grid gap-3 sm:grid-cols-2">
          {career.estimated_months && (
            <div className="flex items-center gap-3 rounded-2xl bg-muted/50 p-4">
              <Clock size={18} className="shrink-0 text-brand-violet" />
              <div>
                <p className="text-xs text-muted-foreground">{t("timeToJob")}</p>
                <p className="font-semibold">
                  {t("months", { count: career.estimated_months })}
                </p>
              </div>
            </div>
          )}
          {salary && (
            <div className="flex items-center gap-3 rounded-2xl bg-muted/50 p-4">
              <Wallet size={18} className="shrink-0 text-brand-violet" />
              <div>
                <p className="text-xs text-muted-foreground">{t("salaryRange")}</p>
                <p className="font-semibold">{t("perMonth", { amount: salary })}</p>
              </div>
            </div>
          )}
        </div>
        <p className="text-xs text-muted-foreground">{t("salaryNote")}</p>
      </Card>

      <h2 className="font-heading mt-8 text-xl font-semibold">{t("skills")}</h2>
      <ol className="mt-3 grid gap-2 sm:grid-cols-2">
        {career.skills.map((skill, i) => (
          <li
            key={skill.name}
            className="flex items-center gap-3 rounded-2xl border p-3 text-sm"
          >
            <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-brand-violet/15 text-xs font-semibold text-violet-700 dark:text-brand-violet-light">
              {i + 1}
            </span>
            <span className="min-w-0 break-words">{ct.skill(skill.name)}</span>
          </li>
        ))}
      </ol>

      <h2 className="font-heading mt-8 text-xl font-semibold">{t("resources")}</h2>
      <p className="text-sm text-muted-foreground">{t("resourcesNote")}</p>
      <ul className="mt-3 grid gap-3 sm:grid-cols-2">
        {career.resources.map((resource) => (
          <li key={resource.url}>
            <a
              href={resource.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex h-full items-start gap-3 rounded-2xl border p-4 transition hover:bg-muted/50"
            >
              <div className="min-w-0 flex-1">
                <p className="line-clamp-2 text-sm font-medium">{resource.title}</p>
                <p className="mt-1 truncate text-xs text-muted-foreground">
                  {[resource.provider, t(`resourceType.${resource.type}`)]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
              </div>
              <ExternalLink size={14} className="mt-0.5 shrink-0 text-muted-foreground" />
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
