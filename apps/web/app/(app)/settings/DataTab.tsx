"use client";

import { useState } from "react";
import { Download } from "lucide-react";
import { toast } from "sonner";

import { api } from "@/lib/api";

import { Card } from "@/components/ui/card";
import LoadingButton from "@/components/shared/LoadingButton";

export default function DataTab() {
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

      toast.success("Your data was downloaded.");
    } catch {
      toast.error("Couldn't prepare your data. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="max-w-xl p-7">
      <h2 className="text-sm font-semibold">Your data</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Download a copy of what Uraan AI stores about you as a JSON file: your
        profile, settings, roadmaps, documents, portfolio, interviews, mentor
        conversations and XP.
      </p>
      <LoadingButton
        type="button"
        className="mt-5 gap-2"
        loading={busy}
        onClick={download}
      >
        <Download size={15} /> Download my data
      </LoadingButton>
    </Card>
  );
}
