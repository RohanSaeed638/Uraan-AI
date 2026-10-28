"use client";

import { useTranslations } from "next-intl";
import { toast } from "sonner";

import { Card } from "@/components/ui/card";
import LanguageSwitcher from "@/components/shared/LanguageSwitcher";
import ThemeToggle from "@/components/shared/ThemeToggle";

export default function AppearanceTab() {
  const t = useTranslations("settings.appearance");

  return (
    <div className="space-y-6">
      <Card className="max-w-xl p-7">
        <h2 className="text-sm font-semibold">{t("title")}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{t("text")}</p>
        <div className="mt-5">
          <ThemeToggle onSaveError={() => toast.error(t("saveFailed"))} />
        </div>
      </Card>

      <Card className="max-w-xl p-7">
        <h2 className="text-sm font-semibold">{t("languageTitle")}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{t("languageText")}</p>
        <div className="mt-5">
          <LanguageSwitcher />
        </div>
      </Card>
    </div>
  );
}
