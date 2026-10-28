"use client";

import { Loader2 } from "lucide-react";
import { useTranslations } from "next-intl";

export default function LoadingAnimation() {
  const t = useTranslations("onboarding.loading");

  return (
    <div className="flex flex-col items-center justify-center py-16">
      <Loader2 className="h-12 w-12 animate-spin text-brand-violet" />

      <h2 className="mt-8 text-2xl font-semibold">
        {t("title")}
      </h2>

      <p className="mt-3 text-muted-foreground">
        {t("text")}
      </p>
    </div>
  );
}