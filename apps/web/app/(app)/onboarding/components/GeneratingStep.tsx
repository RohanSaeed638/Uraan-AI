"use client";

import { Loader2 } from "lucide-react";
import { useTranslations } from "next-intl";
import WelcomeBirdIllustration from "@/components/illustrations/WelcomeBirdIllustration";

export default function GeneratingStep() {
  const t = useTranslations("onboarding.generating");

  return (
    <div className="flex min-h-[75vh] flex-col items-center justify-center text-center">
      <WelcomeBirdIllustration size={110} />

      <h1 className="font-heading mt-4 text-3xl font-bold">
        {t("title")}
      </h1>

      <p className="mt-4 max-w-lg text-muted-foreground">
        {t("text")}
      </p>

      <div className="mt-10 w-full max-w-md">
        <div className="mb-5 flex items-center justify-center gap-2 text-sm text-muted-foreground">
          <Loader2 size={15} className="animate-spin text-brand-violet" />
          {t("wait")}
        </div>

        <div className="mb-5 h-2 overflow-hidden rounded-full bg-muted">
          <div className="h-full w-3/4 animate-pulse rounded-full bg-brand-gradient" />
        </div>

        <ul className="space-y-3 text-start text-sm text-muted-foreground">
          <li>{t("s1")}</li>
          <li>{t("s2")}</li>
          <li>{t("s3")}</li>
          <li>{t("s4")}</li>
          <li>{t("s5")}</li>
        </ul>
      </div>
    </div>
  );
}
