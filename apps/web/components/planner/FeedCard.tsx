"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { CalendarPlus, Copy, RefreshCw } from "lucide-react";

import { regenerateCalendarLink } from "@/lib/api/calendar";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

/** The private link that puts the study plan in Google, Apple or Outlook
 * calendar. Anyone with the link can see the plan, so it can be replaced. */
export default function FeedCard({
  initialToken,
  apiUrl,
}: {
  initialToken: string | null;
  apiUrl: string;
}) {
  const t = useTranslations("planner.feed");
  const [token, setToken] = useState(initialToken);
  const [busy, setBusy] = useState(false);

  const url = token ? `${apiUrl}/calendar/feed/${token}.ics` : null;

  async function copy() {
    if (!url) return;

    try {
      await navigator.clipboard.writeText(url);
      toast.success(t("copied"));
    } catch {
      toast.error(t("copyFailed"));
    }
  }

  async function replace() {
    if (!window.confirm(t("confirmNew"))) return;

    setBusy(true);

    try {
      setToken(await regenerateCalendarLink());
      toast.success(t("newLink"));
    } catch {
      toast.error(t("newLinkFailed"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="gap-3 p-5">
      <p className="flex items-center gap-2 text-sm font-semibold">
        <CalendarPlus size={16} className="text-brand-gold" /> {t("title")}
      </p>
      <p className="text-sm text-muted-foreground">{t("text")}</p>

      {url ? (
        <div className="flex flex-wrap gap-2">
          <Input readOnly value={url} aria-label={t("title")} className="min-w-0 flex-1 text-xs" />
          <Button variant="soft" size="sm" className="gap-1.5" onClick={copy}>
            <Copy size={14} /> {t("copy")}
          </Button>
          <Button variant="outline" size="sm" className="gap-1.5" disabled={busy} onClick={replace}>
            <RefreshCw size={14} /> {t("replace")}
          </Button>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">{t("unavailable")}</p>
      )}

      <p className="text-[11px] text-muted-foreground">{t("warning")}</p>
    </Card>
  );
}
