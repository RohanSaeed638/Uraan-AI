import { ArrowRight, Compass, Sparkles, Target, TrendingUp, Wrench } from "lucide-react";
import Link from "next/link";
import { getTranslations } from "next-intl/server";

import LandingRedirect from "@/components/site/LandingRedirect";
import SiteFooter from "@/components/site/SiteFooter";
import SiteHeader from "@/components/site/SiteHeader";
import { buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const features = [
  { icon: Sparkles, key: "f1" },
  { icon: Target, key: "f2" },
  { icon: TrendingUp, key: "f3" },
  { icon: Wrench, key: "f4" },
] as const;

const careers = ["c1", "c2", "c3", "c4", "c5", "c6"] as const;
const steps = ["s1", "s2", "s3"] as const;
const questions = ["q1", "q2", "q3", "q4"] as const;

export default async function HomePage() {
  const t = await getTranslations("landing");

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <LandingRedirect />
      <SiteHeader />

      <main id="main" tabIndex={-1} className="flex-1 outline-none">
        <section className="mx-auto max-w-4xl px-4 py-16 text-center sm:px-6 sm:py-24">
          <h1 className="font-heading text-4xl font-bold leading-tight sm:text-5xl">{t("title")}</h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-muted-foreground">{t("subtitle")}</p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link href="/register" className={buttonVariants({ size: "lg" })}>
              {t("start")} <ArrowRight className="size-4 rtl:rotate-180" aria-hidden />
            </Link>
            <Link href="/login" className={buttonVariants({ size: "lg", variant: "outline" })}>
              {t("signInShort")}
            </Link>
          </div>
        </section>

        <section aria-labelledby="careers-h" className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
          <h2 id="careers-h" className="font-heading text-2xl font-bold">{t("careersTitle")}</h2>
          <p className="mt-2 text-muted-foreground">{t("careersText")}</p>
          <div className="mt-6 flex flex-wrap gap-3">
            {careers.map((k) => (
              <Link
                key={k}
                href="/register"
                className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-sm font-medium hover:border-brand-violet"
              >
                <Compass className="size-4 text-violet-700 dark:text-brand-violet-light" aria-hidden />
                {t(k)}
              </Link>
            ))}
          </div>
        </section>

        <section aria-labelledby="features-h" className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
          <h2 id="features-h" className="font-heading text-2xl font-bold">{t("featuresTitle")}</h2>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {features.map(({ icon: Icon, key }) => (
              <Card key={key} className="gap-3 p-6">
                <span className="flex size-10 items-center justify-center rounded-xl bg-brand-violet/15 text-violet-700 dark:text-brand-violet-light">
                  <Icon className="size-5" aria-hidden />
                </span>
                <h3 className="font-semibold">{t(key)}</h3>
                <p className="text-sm text-muted-foreground">{t(`${key}Text`)}</p>
              </Card>
            ))}
          </div>
        </section>

        <section aria-labelledby="how-h" className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
          <h2 id="how-h" className="font-heading text-2xl font-bold">{t("howTitle")}</h2>
          <ol className="mt-6 grid gap-4 md:grid-cols-3">
            {steps.map((k, i) => (
              <li key={k}>
                <Card className="h-full gap-2 p-6">
                  <span className="font-mono text-3xl font-bold text-violet-700 dark:text-brand-violet-light">{i + 1}</span>
                  <h3 className="font-semibold">{t(k)}</h3>
                  <p className="text-sm text-muted-foreground">{t(`${k}Text`)}</p>
                </Card>
              </li>
            ))}
          </ol>
        </section>

        <section aria-labelledby="faq-h" className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
          <h2 id="faq-h" className="font-heading text-2xl font-bold">{t("faqTitle")}</h2>
          <div className="mt-6 divide-y divide-border rounded-2xl border border-border bg-card">
            {questions.map((k) => (
              <details key={k} className="group p-5">
                <summary className="cursor-pointer list-none font-medium marker:hidden">{t(k)}</summary>
                <p className="mt-3 text-muted-foreground">{t(`${k}a`)}</p>
              </details>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-4xl px-4 py-16 text-center sm:px-6">
          <h2 className="font-heading text-3xl font-bold">{t("ctaTitle")}</h2>
          <p className="mt-3 text-muted-foreground">{t("ctaText")}</p>
          <Link href="/register" className={buttonVariants({ size: "lg", className: "mt-7" })}>
            {t("start")}
          </Link>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
