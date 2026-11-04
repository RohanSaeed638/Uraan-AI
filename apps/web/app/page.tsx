import { ArrowRight, Compass, Sparkles, Target, TrendingUp, Wrench } from "lucide-react";
import Link from "next/link";
import { getTranslations } from "next-intl/server";

import HeroBackground from "@/components/site/HeroBackground";
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
        <section className="relative isolate">
          <HeroBackground />
          <div className="mx-auto max-w-4xl px-4 pb-24 pt-16 text-center sm:px-6 sm:pb-32 sm:pt-24">
            <p className="mx-auto inline-flex items-center gap-2 rounded-full border border-violet-300/60 bg-white/60 px-4 py-1.5 text-sm font-medium text-violet-800 shadow-sm backdrop-blur dark:border-violet-400/30 dark:bg-white/5 dark:text-violet-200">
              <Sparkles className="size-4 text-amber-500" aria-hidden />
              {t("badge")}
            </p>
            <h1 className="font-heading mt-6 bg-gradient-to-br from-violet-950 via-violet-700 to-indigo-600 bg-clip-text text-4xl font-bold leading-tight text-transparent sm:text-6xl dark:from-white dark:via-violet-200 dark:to-violet-400">
              {t("title")}
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground sm:text-xl">{t("subtitle")}</p>
            <div className="mt-10 flex flex-wrap justify-center gap-3">
              <Link
                href="/register"
                className={buttonVariants({
                  size: "lg",
                  className: "h-12 px-7 text-base shadow-lg shadow-violet-500/30 transition hover:-translate-y-0.5",
                })}
              >
                {t("start")} <ArrowRight className="size-4 rtl:rotate-180" aria-hidden />
              </Link>
              <Link
                href="/login"
                className={buttonVariants({
                  size: "lg",
                  variant: "outline",
                  className: "h-12 bg-white/60 px-7 text-base backdrop-blur dark:bg-white/5",
                })}
              >
                {t("signInShort")}
              </Link>
            </div>
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
                className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-sm font-medium shadow-sm transition hover:-translate-y-0.5 hover:border-brand-violet hover:shadow-md"
              >
                <Compass className="size-4 text-violet-700 dark:text-brand-violet-light" aria-hidden />
                {t(k)}
              </Link>
            ))}
          </div>
        </section>

        <section aria-labelledby="features-h" className="bg-gradient-to-b from-transparent via-violet-500/[0.06] to-transparent">
         <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
          <h2 id="features-h" className="font-heading text-2xl font-bold">{t("featuresTitle")}</h2>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {features.map(({ icon: Icon, key }) => (
              <Card key={key} className="card-lift gap-3 p-6">
                <span className="flex size-11 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 text-white shadow-md shadow-violet-500/30">
                  <Icon className="size-5" aria-hidden />
                </span>
                <h3 className="font-semibold">{t(key)}</h3>
                <p className="text-sm text-muted-foreground">{t(`${key}Text`)}</p>
              </Card>
            ))}
          </div>
         </div>
        </section>

        <section aria-labelledby="how-h" className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
          <h2 id="how-h" className="font-heading text-2xl font-bold">{t("howTitle")}</h2>
          <ol className="mt-6 grid gap-4 md:grid-cols-3">
            {steps.map((k, i) => (
              <li key={k}>
                <Card className="h-full gap-2 p-6">
                  <span className="flex size-11 items-center justify-center rounded-full bg-gradient-to-br from-violet-600 to-indigo-600 font-mono text-lg font-bold text-white shadow-md shadow-violet-500/30">{i + 1}</span>
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

        <section className="mx-auto max-w-5xl px-4 pb-20 pt-6 sm:px-6">
          <div className="relative isolate overflow-hidden rounded-3xl bg-gradient-to-br from-violet-700 via-violet-600 to-indigo-800 px-6 py-14 text-center text-white shadow-2xl shadow-violet-900/20 sm:px-12">
            <div aria-hidden className="absolute inset-0 -z-10 [background-image:radial-gradient(circle,rgba(255,255,255,0.22)_1px,transparent_1.6px)] [background-size:22px_22px] [mask-image:radial-gradient(ellipse_80%_80%_at_50%_50%,black,transparent)]" />
            <div aria-hidden className="absolute -end-16 -top-16 -z-10 size-64 rounded-full bg-amber-300/40 blur-3xl" />
            <div aria-hidden className="absolute -bottom-20 -start-16 -z-10 size-64 rounded-full bg-fuchsia-400/30 blur-3xl" />
            <h2 className="font-heading text-3xl font-bold sm:text-4xl">{t("ctaTitle")}</h2>
            <p className="mx-auto mt-3 max-w-xl text-violet-100">{t("ctaText")}</p>
            <Link
              href="/register"
              className={buttonVariants({
                size: "lg",
                className: "mt-8 h-12 bg-white px-8 text-base text-violet-800 shadow-lg hover:bg-violet-50",
              })}
            >
              {t("start")} <ArrowRight className="size-4 rtl:rotate-180" aria-hidden />
            </Link>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
