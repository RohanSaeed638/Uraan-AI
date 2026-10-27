import Image from "next/image";
import { getTranslations } from "next-intl/server";
import { Sparkles, Bot, TrendingUp } from "lucide-react";
import Logo from "@/components/shared/Logo";

const features = [
  { icon: Sparkles, label: "feature1" },
  { icon: Bot, label: "feature2" },
  { icon: TrendingUp, label: "feature3" },
] as const;

export default async function AuthBrandPanel() {
  const t = await getTranslations("auth");

  return (
    <div className="relative hidden overflow-hidden lg:flex lg:w-[46%] lg:flex-col lg:justify-between lg:p-10 xl:p-14">
      <Image
        src="/illustrations/onboarding_illustration_dark.png"
        alt=""
        aria-hidden
        fill
        priority
        sizes="46vw"
        className="hidden object-cover object-bottom dark:block"
      />
      <Image
        src="/illustrations/onboarding_illustration_light.png"
        alt=""
        aria-hidden
        fill
        priority
        sizes="46vw"
        className="block object-cover object-bottom dark:hidden"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-background/60 via-transparent to-background/30" />

      <div className="relative">
        <Logo variant="full" size={30} href={null} />
      </div>

      <div className="relative max-w-sm rounded-2xl bg-background/70 p-5 backdrop-blur-sm">
        <h2 className="font-heading text-3xl font-bold">
          {t("brandTitle")}
        </h2>
        <p className="mt-3 text-sm text-muted-foreground">
          {t("brandText")}
        </p>

        <ul className="mt-8 flex flex-col gap-3">
          {features.map(({ icon: Icon, label }) => (
            <li key={label} className="flex items-center gap-3">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-gold/15">
                <Icon size={15} className="text-brand-gold" />
              </span>
              <span className="text-sm font-medium">{t(label)}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
