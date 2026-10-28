"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { History, Pause, Play, RefreshCw, SlidersHorizontal } from "lucide-react";

import {
  adaptRoadmap,
  pauseRoadmap,
  regenerateRoadmap,
  restoreRoadmapVersion,
  resumeRoadmap,
} from "@/lib/api/roadmap-actions";
import { apiErrorMessage } from "@/lib/profile-options";
import { AdaptRequest, Roadmap } from "@/types/roadmap";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import AdaptDialog from "./AdaptDialog";
import JobBanner from "./JobBanner";
import VersionsDialog from "./VersionsDialog";

interface Props {
  roadmap: Roadmap;
  dailyHours: number;
}

/** Pause / resume, update the plan, rebuild it, and its version history. */
export default function RoadmapActions({ roadmap, dailyHours }: Props) {
  const t = useTranslations("roadmapEngine");
  const router = useRouter();

  const [busy, setBusy] = useState(false);
  const [adaptOpen, setAdaptOpen] = useState(false);
  const [rebuildOpen, setRebuildOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);

  const building = roadmap.status === "generating";
  const canChange = !building && roadmap.status !== "failed";
  const hasPlan = roadmap.phases.some((p) => p.tasks.length > 0);

  async function run(action: () => Promise<unknown>, failure: string) {
    setBusy(true);

    try {
      await action();
      router.refresh();
    } catch (err) {
      toast.error(apiErrorMessage(err, failure));
    } finally {
      setBusy(false);
    }
  }

  const toggle = () =>
    run(
      () =>
        roadmap.status === "paused"
          ? resumeRoadmap(roadmap.id)
          : pauseRoadmap(roadmap.id),
      t("actionFailed")
    );

  // Starts the background rebuild; the banner then waits and reloads.
  const rebuild = async () => {
    setRebuildOpen(false);
    await run(() => regenerateRoadmap(roadmap.id), t("rebuild.failed"));
  };

  return (
    <>
      <div className="mt-6 flex flex-wrap gap-2">
        {(roadmap.status === "active" || roadmap.status === "paused") && (
          <Button variant="outline" size="sm" className="gap-2" disabled={busy} onClick={toggle}>
            {roadmap.status === "paused" ? <Play size={14} /> : <Pause size={14} />}
            {roadmap.status === "paused" ? t("resume") : t("pause")}
          </Button>
        )}

        {canChange && hasPlan && (
          <Button
            variant="outline"
            size="sm"
            className="gap-2"
            disabled={busy}
            onClick={() => setAdaptOpen(true)}
          >
            <SlidersHorizontal size={14} />
            {t("adapt.open")}
          </Button>
        )}

        {canChange && (
          <Button
            variant="outline"
            size="sm"
            className="gap-2"
            disabled={busy}
            onClick={() => setRebuildOpen(true)}
          >
            <RefreshCw size={14} />
            {t("rebuild.open")}
          </Button>
        )}

        {!building && (
          <Button
            variant="outline"
            size="sm"
            className="gap-2"
            disabled={busy}
            onClick={() => setHistoryOpen(true)}
          >
            <History size={14} />
            {t("versions.open")}
          </Button>
        )}
      </div>

      <JobBanner
        roadmap={roadmap}
        busy={busy}
        onResume={toggle}
        onRetry={rebuild}
      />

      <AdaptDialog
        open={adaptOpen}
        onOpenChange={setAdaptOpen}
        currentHours={dailyHours}
        onSubmit={async (request: AdaptRequest) => {
          await adaptRoadmap(roadmap.id, request);
          router.refresh();
        }}
      />

      <VersionsDialog
        roadmapId={roadmap.id}
        open={historyOpen}
        onOpenChange={setHistoryOpen}
        onRestore={async (version) => {
          await restoreRoadmapVersion(roadmap.id, version.id);
          toast.success(t("versions.restored"));
          router.refresh();
        }}
      />

      <Dialog open={rebuildOpen} onOpenChange={setRebuildOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t("rebuild.title")}</DialogTitle>
            <DialogDescription>{t("rebuild.description")}</DialogDescription>
          </DialogHeader>

          <p className="text-sm text-muted-foreground">{t("rebuild.warning")}</p>

          <div className="flex flex-wrap gap-2">
            <Button onClick={rebuild}>{t("rebuild.confirm")}</Button>
            <Button variant="ghost" onClick={() => setRebuildOpen(false)}>
              {t("rebuild.cancel")}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
