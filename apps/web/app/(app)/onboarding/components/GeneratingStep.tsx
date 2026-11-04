"use client";

import { CircleCheck, Loader2 } from "lucide-react";
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

        {/* The first steps are shown as done, the rest as still going. */}
        <ul className="space-y-3 text-start text-sm text-muted-foreground">
          {(["s1", "s2", "s3", "s4", "s5"] as const).map((key, index) => (
            <li key={key} className="flex items-center gap-3">
              {index < 2 ? (
                <CircleCheck size={16} className="shrink-0 text-emerald-500" aria-hidden />
              ) : (
                <Loader2 size={16} className="shrink-0 animate-spin text-brand-violet/70" aria-hidden />
              )}
              {t(key)}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
