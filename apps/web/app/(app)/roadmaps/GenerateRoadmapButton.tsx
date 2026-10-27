"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

import { Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import GenerateRoadmapDialog from "./GenerateRoadmapDialog";

export default function GenerateRoadmapButton({
  defaultCareer,
}: {
  defaultCareer?: string;
}) {
  const t = useTranslations("roadmaps");

  // Arriving from a career page opens the dialog with that career chosen.
  const [open, setOpen] = useState(!!defaultCareer);


  return (
    <>
    <Button
      onClick={() => setOpen(true)}
    >
        <>
          <Sparkles className="me-2 h-4 w-4" />
          {t("generate")}
        </>
    </Button>
    <GenerateRoadmapDialog
      open={open}
      onOpenChange={setOpen}
      defaultCareer={defaultCareer}
    />
    </>
  );
}