import type { Metadata } from "next";
import { Check } from "lucide-react";
import Link from "next/link";
import { getTranslations } from "next-intl/server";

import { buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("site");
  return { title: t("pricing"), description: t("pricingIntro") };
}

export default async function PricingPage() {
  const t = await getTranslations("site");
  const included = ["p1", "p2", "p3", "p4", "p5"] as const;

  return (
    <div className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
      <h1 className="font-heading text-3xl font-bold sm:text-4xl">{t("pricingTitle")}</h1>
      <p className="mt-4 text-lg text-muted-foreground">{t("pricingIntro")}</p>
      <Card className="mt-10 gap-5 p-7">
        <div>
          <p className="text-sm font-medium text-violet-700 dark:text-brand-violet-light">{t("betaPlan")}</p>
          <p className="mt-1 font-mono text-4xl font-bold">{t("free")}</p>
        </div>
        <ul className="space-y-3">
          {included.map((k) => (
            <li key={k} className="flex items-start gap-3">
              <Check className="mt-0.5 size-5 shrink-0 text-violet-700 dark:text-brand-violet-light" aria-hidden />
              <span>{t(k)}</span>
            </li>
          ))}
        </ul>
        <Link href="/register" className={buttonVariants({ size: "lg", className: "w-full sm:w-fit" })}>
          {t("start")}
        </Link>
      </Card>
      <p className="mt-6 text-sm text-muted-foreground">{t("pricingNote")}</p>
    </div>
  );
}
