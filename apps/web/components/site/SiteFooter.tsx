import Link from "next/link";
import { getTranslations } from "next-intl/server";

export default async function SiteFooter() {
  const t = await getTranslations("site");

  return (
    <footer className="border-t border-border py-8 text-sm text-muted-foreground">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 sm:px-6">
        <p>{t("copyright", { year: new Date().getFullYear() })}</p>
        <nav aria-label={t("footerLabel")} className="flex flex-wrap gap-x-5 gap-y-2">
          <Link href="/about" className="hover:text-foreground">{t("about")}</Link>
          <Link href="/pricing" className="hover:text-foreground">{t("pricing")}</Link>
          <Link href="/terms" className="hover:text-foreground">{t("terms")}</Link>
          <Link href="/privacy" className="hover:text-foreground">{t("privacy")}</Link>
          <Link href="/contact" className="hover:text-foreground">{t("contact")}</Link>
          <Link href="/login" className="hover:text-foreground">{t("signIn")}</Link>
        </nav>
      </div>
    </footer>
  );
}
