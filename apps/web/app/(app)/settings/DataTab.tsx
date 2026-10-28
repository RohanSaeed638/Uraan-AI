"use client";

import { useState } from "react";
import { Download } from "lucide-react";
import { toast } from "sonner";
import { useTranslations } from "next-intl";

import { api } from "@/lib/api";

import { Card } from "@/components/ui/card";
import LoadingButton from "@/components/shared/LoadingButton";

export default function DataTab() {
  const t = useTranslations("settings.data");
  const [busy, setBusy] = useState(false);

  async function download() {
    setBusy(true);

    try {
      const { data } = await api.get<Blob>("/account/export", {
        responseType: "blob",
      });

      const url = URL.createObjectURL(data);
      const link = document.createElement("a");
      const day = new Date().toISOString().slice(0, 10);

      link.href = url;
      link.download = `uraan-ai-data-${day}.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);

      toast.success(t("done"));
    } catch {
      toast.error(t("failed"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="max-w-xl p-7">
      <h2 className="text-sm font-semibold">{t("title")}</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        {t("text")}
      </p>
      <LoadingButton
        type="button"
        className="mt-5 gap-2"
        loading={busy}
        onClick={download}
      >
        <Download size={15} /> {t("download")}
      </LoadingButton>
    </Card>
  );
}
