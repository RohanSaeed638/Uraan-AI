"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { useTranslations } from "next-intl";

import {
  disablePush,
  enablePush,
  getPushStatus,
  PushStatus,
} from "@/lib/push";

import { Button } from "@/components/ui/button";

export default function PushToggle() {
  const t = useTranslations("settings.push");
  const [status, setStatus] = useState<PushStatus | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getPushStatus()
      .then((s) => !cancelled && setStatus(s))
      .catch(() => !cancelled && setStatus("unsupported"));
    return () => {
      cancelled = true;
    };
  }, []);

  async function toggle() {
    setBusy(true);
    try {
      const next = status === "on" ? await disablePush() : await enablePush();
      setStatus(next);
      if (next === "on") toast.success(t("on"));
    } catch {
      toast.error(t("failed"));
    } finally {
      setBusy(false);
    }
  }

  if (status === null) return null;

  const canToggle = status === "on" || status === "off";

  return (
    <div className="flex items-start justify-between gap-4">
      <span>
        <span className="block text-sm font-medium">
          {t("title")}
        </span>
        <span className="block text-xs text-muted-foreground">
          {status === "unsupported" || status === "unconfigured" || status === "denied"
            ? t(status)
            : t("default")}
        </span>
      </span>
      {canToggle && (
        <Button
          type="button"
          size="sm"
          variant={status === "on" ? "outline" : "default"}
          disabled={busy}
          onClick={toggle}
        >
          {status === "on" ? t("turnOff") : t("turnOn")}
        </Button>
      )}
    </div>
  );
}
