import { useTranslations } from "next-intl";

/** "just now", "5m ago", "3h ago", "2d ago" in the app's language. */
export function useTimeAgo() {
  const t = useTranslations("notifications");

  return (iso: string) => {
    const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000);

    if (minutes < 1) return t("justNow");
    if (minutes < 60) return t("minutes", { count: minutes });

    const hours = Math.round(minutes / 60);

    if (hours < 24) return t("hours", { count: hours });

    return t("days", { count: Math.round(hours / 24) });
  };
}
