"use client";

import { WifiOff } from "lucide-react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";

export default function OfflinePage() {
  const t = useTranslations("errorPages");

  return (
    <main id="main" className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background p-6 text-center">
      <WifiOff className="size-12 text-brand-violet" aria-hidden />
      <h1 className="font-heading text-2xl font-bold">{t("offlineTitle")}</h1>
      <p className="max-w-md text-muted-foreground">{t("offlineText")}</p>
      <Button size="lg" onClick={() => window.location.reload()}>
        {t("retry")}
      </Button>
    </main>
  );
}
