import Link from "next/link";
import { getTranslations } from "next-intl/server";

import { buttonVariants } from "@/components/ui/button";

export default async function NotFound() {
  const t = await getTranslations("errorPages");

  return (
    <main id="main" className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background p-6 text-center">
      <p className="font-mono text-6xl font-bold text-brand-violet">404</p>
      <h1 className="font-heading text-2xl font-bold">{t("notFoundTitle")}</h1>
      <p className="max-w-md text-muted-foreground">{t("notFoundText")}</p>
      <Link href="/" className={buttonVariants({ size: "lg" })}>
        {t("home")}
      </Link>
    </main>
  );
}
