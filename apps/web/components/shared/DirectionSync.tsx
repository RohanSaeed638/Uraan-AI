"use client";

import { DirectionProvider } from "@base-ui/react/direction-provider";
import { useLocale } from "next-intl";

import { isRtl } from "@/i18n/config";

/** Tells the library components (sliders, menus, selects) which way the text runs. */
export default function DirectionSync({ children }: { children: React.ReactNode }) {
  const locale = useLocale();

  return (
    <DirectionProvider direction={isRtl(locale) ? "rtl" : "ltr"}>{children}</DirectionProvider>
  );
}
