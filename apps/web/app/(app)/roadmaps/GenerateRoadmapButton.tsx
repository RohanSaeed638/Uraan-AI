"use client";

import { useState } from "react";

import { Loader2, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import GenerateRoadmapDialog from "./GenerateRoadmapDialog";

export default function GenerateRoadmapButton() {
  const [open, setOpen] = useState(false);


  return (
    <>
    <Button
      onClick={() => setOpen(true)}
    >
        <>
          <Sparkles className="mr-2 h-4 w-4" />
          Generate Roadmap
        </>
    </Button>
    <GenerateRoadmapDialog open={open} onOpenChange={setOpen}/>
    </>
  );
}