"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import { authErrorKey } from "@/lib/auth-errors";
import { authService } from "@/services/auth/auth";

import { Button } from "@/components/ui/button";

// Supabase allows one confirmation email a minute per address.
const WAIT_SECONDS = 60;

/** "Send the confirmation email again", with a short wait so it cannot be spammed. */
export default function ResendConfirmation({ email }: { email: string }) {
  const t = useTranslations("auth");
  const tErrors = useTranslations("auth.errors");

  const [sending, setSending] = useState(false);
  const [wait, setWait] = useState(0);

  useEffect(() => {
    if (wait <= 0) return;

    const timer = setTimeout(() => setWait((seconds) => seconds - 1), 1000);

    return () => clearTimeout(timer);
  }, [wait]);

  async function resend() {
    setSending(true);

    try {
      const { error } = await authService.resendConfirmation(email);

      if (error) {
        const key = authErrorKey(error.message);

        toast.error(key ? tErrors(key) : t("resendFailed"));

        // Told to slow down: wait out the minute before offering it again.
        if (key === "rateLimited") setWait(WAIT_SECONDS);

        return;
      }

      toast.success(t("resent"));
      setWait(WAIT_SECONDS);
    } catch {
      toast.error(t("resendFailed"));
    } finally {
      setSending(false);
    }
  }

  return (
    <Button type="button" variant="outline" disabled={sending || wait > 0} onClick={resend}>
      {wait > 0 ? t("resendWait", { seconds: wait }) : t("resend")}
    </Button>
  );
}
