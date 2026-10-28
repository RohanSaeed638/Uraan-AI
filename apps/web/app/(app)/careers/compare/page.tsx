import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { ArrowLeft } from "lucide-react";

import { salaryRange } from "@/lib/careers";
import { careerText } from "@/lib/career-text";
import { compareCareersServer } from "@/lib/server/data";
import { CareerDetail } from "@/types/api";

import { buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default async function ComparePage({
  searchParams,
}: {
  searchParams: Promise<{ slugs?: string }>;
}) {
  const t = await getTranslations("careers");
  const ct = careerText(await getTranslations("catalog"));
  const { slugs } = await searchParams;

  const wanted = [...new Set((slugs ?? "").split(",").filter(Boolean))].slice(0, 4);
  const careers = wanted.length >= 2 ? await compareCareersServer(wanted) : null;

  if (!careers) {
    return (
      <main className="mx-auto max-w-3xl">
        <Card className="items-center gap-4 p-8 text-center">
          <p className="text-sm text-muted-foreground">{t("compareNeedTwo")}</p>
          <Link href="/careers" className={buttonVariants({})}>
            {t("backToCareers")}
          </Link>
        </Card>
      </main>
    );
  }

  const skillCounts = new Map<string, number>();
  careers.forEach((c) =>
    c.skills.forEach((s) => skillCounts.set(s.name, (skillCounts.get(s.name) ?? 0) + 1))
  );
  const shared = [...skillCounts].filter(([, n]) => n === careers.length).map(([name]) => name);

  const rows: { label: string; value: (c: CareerDetail) => string }[] = [
    { label: t("salaryRange"), value: (c) => salaryRange(c.salary_min_pkr, c.salary_max_pkr) ?? "-" },
    { label: t("timeToJob"), value: (c) => (c.estimated_months ? t("months", { count: c.estimated_months }) : "-") },
    { label: t("demandRow"), value: (c) => (c.market_demand ? t(`demand.${c.market_demand}`) : "-") },
    { label: t("difficultyRow"), value: (c) => (c.difficulty ? t(`difficulty.${c.difficulty}`) : "-") },
    { label: t("skillsRow"), value: (c) => String(c.skills.length) },
  ];

  return (
    <main className="mx-auto max-w-5xl">
      <Link
        href="/careers"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft size={14} className="rtl:rotate-180" /> {t("backToCareers")}
      </Link>

      <h1 className="font-heading text-3xl font-bold">{t("compareTitle")}</h1>

      <Card className="mt-6 overflow-x-auto p-0">
        <table className="w-full min-w-[560px] text-sm">
          <thead>
            <tr className="border-b text-start">
              <th scope="col" className="w-36 p-4" />
              {careers.map((c) => (
                <th key={c.slug} scope="col" className="p-4 align-top">
                  <Link
                    href={`/careers/${c.slug}`}
                    className="font-heading text-base font-semibold hover:underline"
                  >
                    {ct.name(c.slug, c.name)}
                  </Link>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label} className="border-b last:border-0">
                <th scope="row" className="p-4 text-start font-medium text-muted-foreground">
                  {row.label}
                </th>
                {careers.map((c) => (
                  <td key={c.slug} className="p-4">
                    {row.value(c)}
                  </td>
                ))}
              </tr>
            ))}
            <tr>
              <th scope="row" className="p-4 text-start align-top font-medium text-muted-foreground">
                {t("topSkills")}
              </th>
              {careers.map((c) => (
                <td key={c.slug} className="p-4 align-top">
                  <ul className="space-y-1">
                    {c.skills.slice(0, 5).map((s) => (
                      <li key={s.name} className="break-words">
                        {ct.skill(s.name)}
                      </li>
                    ))}
                  </ul>
                </td>
              ))}
            </tr>
            <tr className="border-t">
              <td className="p-4" />
              {careers.map((c) => (
                <td key={c.slug} className="p-4">
                  <Link
                    href={`/roadmaps?career=${c.slug}`}
                    className={buttonVariants({ size: "sm" })}
                  >
                    {t("generateRoadmap")}
                  </Link>
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </Card>

      {shared.length > 0 && (
        <p className="mt-4 text-sm text-muted-foreground">
          {t("sharedSkills", { skills: shared.map(ct.skill).join(", ") })}
        </p>
      )}
    </main>
  );
}
