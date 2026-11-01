import type { Metadata } from "next";
import { Mail } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { CONTACT_EMAIL } from "@/lib/site";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("contact");
  return { title: t("title"), description: t("intro") };
}

export default async function ContactPage() {
  const t = await getTranslations("contact");
  const topics = ["t1", "t2", "t3", "t4"] as const;

  return (
    <div className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
      <h1 className="font-heading text-3xl font-bold sm:text-4xl">{t("title")}</h1>
      <p className="mt-4 text-lg text-muted-foreground">{t("intro")}</p>

      <Card className="mt-10 gap-4 p-7">
        <p className="flex items-center gap-2 font-semibold">
          <Mail className="size-5 text-violet-700 dark:text-brand-violet-light" aria-hidden />
          {t("emailUs")}
        </p>

        {CONTACT_EMAIL ? (
          <a href={`mailto:${CONTACT_EMAIL}`} className={buttonVariants({ size: "lg", className: "w-fit" })}>
            {CONTACT_EMAIL}
          </a>
        ) : (
          <p className="text-sm text-muted-foreground">{t("notConfigured")}</p>
        )}

        <div>
          <p className="text-sm font-medium">{t("helpWith")}</p>
          <ul className="mt-2 list-disc space-y-1 ps-6 text-sm text-muted-foreground">
            {topics.map((k) => (
              <li key={k}>{t(k)}</li>
            ))}
          </ul>
        </div>

        <p className="text-sm text-muted-foreground">{t("include")}</p>
      </Card>
    </div>
  );
}
