"use client";

import * as Sentry from "@sentry/nextjs";
import { useTranslations } from "next-intl";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";

export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const t = useTranslations("errorPages");

  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <main id="main" className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background p-6 text-center">
      <p className="font-mono text-6xl font-bold text-brand-violet">500</p>
      <h1 className="font-heading text-2xl font-bold">{t("errorTitle")}</h1>
      <p className="max-w-md text-muted-foreground">{t("errorText")}</p>
      <Button size="lg" onClick={reset}>
        {t("retry")}
      </Button>
    </main>
  );
}
