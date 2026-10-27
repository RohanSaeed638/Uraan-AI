"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { Loader2, PauseCircle, TriangleAlert } from "lucide-react";

import { waitForRoadmap } from "@/services/roadmap";
import { Roadmap } from "@/types/roadmap";

import { Button } from "@/components/ui/button";

interface Props {
  roadmap: Roadmap;
  onResume: () => void;
  onRetry: () => void;
  busy: boolean;
}

/** The state of the roadmap that needs saying: building, paused, or failed. */
export default function JobBanner({ roadmap, onResume, onRetry, busy }: Props) {
  const t = useTranslations("roadmapEngine.banner");
  const router = useRouter();

  const building = roadmap.status === "generating";

  // While the roadmap is being (re)built, wait for it, then load the result.
  useEffect(() => {
    if (!building) return;

    let cancelled = false;

    waitForRoadmap(roadmap.id)
      .catch(() => null)
      .then(() => {
        if (!cancelled) router.refresh();
      });

    return () => {
      cancelled = true;
    };
  }, [building, roadmap.id, router]);

  if (building) {
    return (
      <div
        role="status"
        className="mt-4 flex items-start gap-3 rounded-2xl border border-brand-violet/30 bg-brand-violet/10 p-4 text-sm"
      >
        <Loader2 size={18} className="mt-0.5 shrink-0 animate-spin text-brand-violet" />
        <div>
          <p className="font-medium">{t("buildingTitle")}</p>
          <p className="mt-0.5 text-muted-foreground">{t("buildingText")}</p>
        </div>
      </div>
    );
  }

  if (roadmap.status === "failed") {
    return (
      <div
        role="alert"
        className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-destructive/30 bg-destructive/10 p-4 text-sm"
      >
        <div className="flex min-w-0 items-start gap-3">
          <TriangleAlert size={18} className="mt-0.5 shrink-0 text-destructive" />
          <p>{roadmap.generation_error ?? t("failed")}</p>
        </div>
        <Button size="sm" variant="outline" disabled={busy} onClick={onRetry}>
          {t("tryAgain")}
        </Button>
      </div>
    );
  }

  if (roadmap.status === "paused") {
    return (
      <div
        role="status"
        className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border bg-muted/50 p-4 text-sm"
      >
        <div className="flex min-w-0 items-start gap-3">
          <PauseCircle size={18} className="mt-0.5 shrink-0 text-muted-foreground" />
          <div>
            <p className="font-medium">{t("pausedTitle")}</p>
            <p className="mt-0.5 text-muted-foreground">{t("pausedText")}</p>
          </div>
        </div>
        <Button size="sm" disabled={busy} onClick={onResume}>
          {t("resume")}
        </Button>
      </div>
    );
  }

  // A rebuild or update that did not work, while the roadmap itself is fine.
  if (roadmap.generation_error) {
    return (
      <div
        role="alert"
        className="mt-4 flex items-start gap-3 rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm"
      >
        <TriangleAlert size={18} className="mt-0.5 shrink-0 text-amber-500" />
        <p>{roadmap.generation_error}</p>
      </div>
    );
  }

  return null;
}
