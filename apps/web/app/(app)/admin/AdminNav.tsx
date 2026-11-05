"use client";

import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";

import FilterChips from "@/components/shared/FilterChips";

const SECTIONS = ["overview", "users", "careers", "resources", "announcements", "audit"] as const;

const HREF = (key: (typeof SECTIONS)[number]) => (key === "overview" ? "/admin" : `/admin/${key}`);

export default function AdminNav() {
  const t = useTranslations("admin.nav");
  const pathname = usePathname();

  const current =
    SECTIONS.find((key) => key !== "overview" && pathname.startsWith(HREF(key))) ?? "overview";

  return (
    <FilterChips
      className="mt-6"
      label={t("label")}
      value={current}
      options={SECTIONS.map((key) => ({ value: key, label: t(key), href: HREF(key) }))}
    />
  );
}
