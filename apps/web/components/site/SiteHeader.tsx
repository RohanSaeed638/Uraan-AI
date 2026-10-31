import Link from "next/link";
import { getTranslations } from "next-intl/server";

import Logo from "@/components/shared/Logo";
import LanguageSwitcher from "@/components/shared/LanguageSwitcher";
import { buttonVariants } from "@/components/ui/button";

export default async function SiteHeader() {
  const t = await getTranslations("site");

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-background/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-4 px-4 sm:px-6">
        <Logo variant="full" size={26} />
        <nav aria-label={t("navLabel")} className="ms-6 hidden items-center gap-5 text-sm font-medium sm:flex">
          <Link href="/about" className="text-muted-foreground hover:text-foreground">{t("about")}</Link>
          <Link href="/pricing" className="text-muted-foreground hover:text-foreground">{t("pricing")}</Link>
        </nav>
        <div className="ms-auto flex items-center gap-2">
          <LanguageSwitcher />
          <Link href="/login" className={buttonVariants({ variant: "ghost", size: "sm" })}>{t("signIn")}</Link>
          <Link href="/register" className={buttonVariants({ size: "sm" })}>{t("start")}</Link>
        </div>
      </div>
    </header>
  );
}
