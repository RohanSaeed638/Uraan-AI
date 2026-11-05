import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("site");
  return { title: t("about"), description: t("aboutIntro") };
}

export default async function AboutPage() {
  const t = await getTranslations("site");
  const points = ["about1", "about2", "about3"] as const;

  return (
    <div className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
      <h1 className="font-heading text-3xl font-bold sm:text-4xl">{t("aboutTitle")}</h1>
      <p className="mt-4 text-lg text-muted-foreground">{t("aboutIntro")}</p>
      <div className="mt-10 space-y-6">
        {points.map((k) => (
          <section key={k}>
            <h2 className="font-heading text-xl font-semibold">{t(`${k}Title`)}</h2>
            <p className="mt-2 text-muted-foreground">{t(`${k}Text`)}</p>
          </section>
        ))}
      </div>
    </div>
  );
}
