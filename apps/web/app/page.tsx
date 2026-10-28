"use client";

import { useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import {
  Sparkles,
  Target,
  TrendingUp,
  Wrench,
  ArrowRight,
  Loader2,
} from "lucide-react";

import { useAuthStore } from "@/store/auth";
import Logo from "@/components/shared/Logo";
import { buttonVariants } from "@/components/ui/button";

const features = [
  { icon: Sparkles, label: "f1" },
  { icon: Target, label: "f2" },
  { icon: TrendingUp, label: "f3" },
  { icon: Wrench, label: "f4" },
] as const;

export default function HomePage() {
  const t = useTranslations("landing");
  const { user, loading } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      router.replace("/dashboard");
    }
  }, [loading, user, router]);

  if (loading || user) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-4 sm:p-8">
      <div className="relative w-full max-w-5xl overflow-hidden rounded-3xl shadow-2xl sm:min-h-[560px]">
        {/* Background illustration — swaps with theme */}
        <Image
          src="/illustrations/onboarding_illustration_dark.png"
          alt=""
          aria-hidden
          fill
          priority
          sizes="(max-width: 1024px) 100vw, 1024px"
          className="hidden object-cover dark:block"
        />
        <Image
          src="/illustrations/onboarding_illustration_light.png"
          alt=""
          aria-hidden
          fill
          priority
          sizes="(max-width: 1024px) 100vw, 1024px"
          className="block object-cover dark:hidden"
        />

        {/* Legibility scrim: solid on the left, fading out over the climber */}
        <div className="absolute inset-0 bg-gradient-to-r from-background via-background/85 to-transparent sm:from-background sm:via-background/75 sm:to-transparent" />

        {/* Content */}
        <div className="relative flex min-h-[560px] flex-col justify-between p-6 sm:p-10">
          <Logo variant="full" size={28} />

          <div className="max-w-md">
            <h1 className="font-heading text-3xl font-bold leading-tight sm:text-4xl">
              {t("title")}
            </h1>
            <p className="mt-3 text-muted-foreground">
              {t("subtitle")}
            </p>

            <ul className="mt-7 flex flex-col gap-3.5">
              {features.map(({ icon: Icon, label }) => (
                <li key={label} className="flex items-center gap-3">
                  <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-brand-gold/15 text-brand-gold">
                    <Icon size={15} />
                  </span>
                  <span className="text-sm font-medium">{t(label)}</span>
                </li>
              ))}
            </ul>

            <div className="mt-8 flex flex-col items-start gap-3 sm:flex-row sm:items-center">
              <Link
                href="/register"
                className={buttonVariants({
                  size: "lg",
                  className: "w-full gap-2 sm:w-auto",
                })}
              >
                {t("start")} <ArrowRight size={16} className="rtl:rotate-180" />
              </Link>
              <p className="text-sm text-muted-foreground">
                {t.rich("haveAccount", {
                  link: (chunks) => (
                    <Link
                      href="/login"
                      className="font-medium text-brand-gold-deep dark:text-brand-gold hover:underline"
                    >
                      {chunks}
                    </Link>
                  ),
                })}
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
