"use client";

import { Loader2 } from "lucide-react";
import WelcomeBirdIllustration from "@/components/illustrations/WelcomeBirdIllustration";

export default function GeneratingStep() {
  return (
    <div className="flex min-h-[75vh] flex-col items-center justify-center text-center">
      <WelcomeBirdIllustration size={110} />

      <h1 className="font-heading mt-4 text-3xl font-bold">
        Creating your AI roadmap
      </h1>

      <p className="mt-4 max-w-lg text-muted-foreground">
        We&apos;re analyzing your goals, experience, learning style and
        available study time.
      </p>

      <div className="mt-10 w-full max-w-md">
        <div className="mb-5 flex items-center justify-center gap-2 text-sm text-muted-foreground">
          <Loader2 size={15} className="animate-spin text-brand-violet" />
          This usually takes a few seconds
        </div>

        <div className="mb-5 h-2 overflow-hidden rounded-full bg-muted">
          <div className="h-full w-3/4 animate-pulse rounded-full bg-brand-gradient" />
        </div>

        <ul className="space-y-3 text-left text-sm text-muted-foreground">
          <li>✅ Selecting roadmap...</li>
          <li>✅ Preparing milestones...</li>
          <li>⏳ Finding projects...</li>
          <li>⏳ Preparing interview plan...</li>
          <li>⏳ Building personalized dashboard...</li>
        </ul>
      </div>
    </div>
  );
}
