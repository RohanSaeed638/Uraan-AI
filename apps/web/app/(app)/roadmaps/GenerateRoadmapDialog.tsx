"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

import GenerateRoadmapForm from "./GenerateRoadmapForm";

import { api } from "@/lib/api/client";

import { GenerateRoadmapFormValues } from "@/types/roadmap";

interface GenerateRoadmapDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function GenerateRoadmapDialog({
  open,
  onOpenChange,
}: GenerateRoadmapDialogProps) {
  const router = useRouter();

  const [loading, setLoading] = useState(false);

  async function handleSubmit(
    values: GenerateRoadmapFormValues
  ) {
    try {
      setLoading(true);

      const response = await api.post(
        "/roadmaps/generate",
        values
      );

      onOpenChange(false);
      console.log("Roadmap generated:", response.data.id);
      router.push(`/roadmaps/${response.data.id}`);
      // router.refresh();
    } catch (error) {
      console.error(
        "Failed to generate roadmap:",
        error
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
      <DialogContent className="sm:max-w-xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            Generate a New Roadmap
          </DialogTitle>

          <DialogDescription>
            Tell us about your current situation so we
            can create a personalized learning plan.
          </DialogDescription>
        </DialogHeader>

        <GenerateRoadmapForm
          loading={loading}
          onSubmit={handleSubmit}
        />
      </DialogContent>
    </Dialog>
  );
}