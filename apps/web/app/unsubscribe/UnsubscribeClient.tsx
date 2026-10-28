"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import axios from "axios";
import { useTranslations } from "next-intl";
import { MailCheck, MailX } from "lucide-react";

import Logo from "@/components/shared/Logo";
import LoadingButton from "@/components/shared/LoadingButton";
import { buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const API = process.env.NEXT_PUBLIC_API_URL;

type State = "checking" | "ready" | "done" | "invalid";

/** One click to stop email. Opening the link changes nothing (mail scanners
 * open links); the button does. */
export default function UnsubscribeClient({ token }: { token: string }) {
  const t = useTranslations("unsubscribe");
  const [state, setState] = useState<State>(token ? "checking" : "invalid");
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!token) return;

    axios
      .get<{ subscribed: boolean }>(`${API}/email/unsubscribe`, { params: { token } })
      .then(({ data }) => setState(data.subscribed ? "ready" : "done"))
      .catch(() => setState("invalid"));
  }, [token]);

  async function unsubscribe() {
    setBusy(true);
    setFailed(false);

    try {
      await axios.post(`${API}/email/unsubscribe`, null, { params: { token } });
      setState("done");
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md items-center gap-5 p-8 text-center">
        <Logo variant="full" size={26} />

        {state === "checking" && <p className="text-sm text-muted-foreground">{t("checking")}</p>}

        {state === "ready" && (
          <>
            <span className="flex size-14 items-center justify-center rounded-full bg-brand-gold/15 text-brand-gold">
              <MailX size={26} />
            </span>
            <h1 className="font-heading text-xl font-bold">{t("title")}</h1>
            <p className="text-sm text-muted-foreground">{t("text")}</p>
            {failed && (
              <p role="alert" className="text-sm text-destructive">
                {t("failed")}
              </p>
            )}
            <LoadingButton loading={busy} onClick={unsubscribe} className="w-full" size="lg">
              {t("confirm")}
            </LoadingButton>
          </>
        )}

        {state === "done" && (
          <>
            <span className="flex size-14 items-center justify-center rounded-full bg-emerald-500/15 text-emerald-500">
              <MailCheck size={26} />
            </span>
            <h1 className="font-heading text-xl font-bold">{t("doneTitle")}</h1>
            <p className="text-sm text-muted-foreground">{t("doneText")}</p>
            <Link
              href="/settings?tab=preferences"
              className={buttonVariants({ variant: "outline", className: "w-full" })}
            >
              {t("settings")}
            </Link>
          </>
        )}

        {state === "invalid" && (
          <>
            <h1 className="font-heading text-xl font-bold">{t("invalidTitle")}</h1>
            <p className="text-sm text-muted-foreground">{t("invalidText")}</p>
            <Link href="/login" className={buttonVariants({ className: "w-full" })}>
              {t("signIn")}
            </Link>
          </>
        )}
      </Card>
    </main>
  );
}
