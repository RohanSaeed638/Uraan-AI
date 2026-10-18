"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import {
  disablePush,
  enablePush,
  getPushStatus,
  PushStatus,
} from "@/lib/push";

import { Button } from "@/components/ui/button";

const messages: Partial<Record<PushStatus, string>> = {
  unsupported: "This browser doesn't support push notifications.",
  unconfigured: "Push notifications aren't set up on the server yet.",
  denied:
    "Notifications are blocked for this site. Allow them in your browser settings, then try again.",
};

export default function PushToggle() {
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
      if (next === "on") toast.success("Push notifications are on.");
    } catch {
      toast.error("Couldn't change push notifications.");
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
          Push notifications on this device
        </span>
        <span className="block text-xs text-muted-foreground">
          {messages[status] ??
            "Get your daily reminder even when Uraan AI is closed."}
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
          {status === "on" ? "Turn off" : "Turn on"}
        </Button>
      )}
    </div>
  );
}
