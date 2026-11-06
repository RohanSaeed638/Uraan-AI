"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

import Illustration from "@/components/illustrations/Illustration";
import RoadmapBuilding from "@/components/roadmap/RoadmapBuilding";

import GenerateRoadmapForm from "./GenerateRoadmapForm";

import { api } from "@/lib/api/client";
import { apiErrorMessage } from "@/lib/profile-options";
import { finishRoadmap, RoadmapJobError } from "@/services/roadmap";

import { GenerateRoadmapFormValues } from "@/types/roadmap";

interface GenerateRoadmapDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  defaultCareer?: string;
}

export default function GenerateRoadmapDialog({
  open,
  onOpenChange,
  defaultCareer,
}: GenerateRoadmapDialogProps) {
  const router = useRouter();
  const t = useTranslations("roadmapForm");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(
    values: GenerateRoadmapFormValues
  ) {
    try {
      setLoading(true);

      setError(null);

      // Returns at once; the roadmap is built in the background.
      const response = await api.post<{ id: string }>(
        "/roadmaps/generate",
        values
      );

      await finishRoadmap(response.data.id);

      onOpenChange(false);
      router.push(`/roadmaps/${response.data.id}`);
    } catch (err) {
      console.error("Failed to generate roadmap:", err);

      setError(
        err instanceof RoadmapJobError
          ? err.message
          : apiErrorMessage(err, t("failed"))
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-xl">
        {loading && <RoadmapBuilding compact title={t("dialogTitle")} />}

        {/* Kept mounted while building, so the answers are still there if it fails. */}
        <div hidden={loading} className="space-y-4">
          <>
            <DialogHeader className="sm:flex-row sm:items-center sm:gap-4">
              <Illustration name="path" size={96} className="hidden sm:block" />

              <div className="min-w-0 space-y-1.5">
                <DialogTitle>{t("dialogTitle")}</DialogTitle>

                <DialogDescription>{t("dialogText")}</DialogDescription>
              </div>
            </DialogHeader>

            {error && (
              <p role="alert" className="rounded-2xl bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </p>
            )}

            <GenerateRoadmapForm loading={loading} onSubmit={handleSubmit} defaultCareer={defaultCareer} />
          </>
        </div>
      </DialogContent>
    </Dialog>
  );
}