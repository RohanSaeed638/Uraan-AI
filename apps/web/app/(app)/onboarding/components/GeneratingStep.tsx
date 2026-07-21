"use client";

import { Loader2, Sparkles } from "lucide-react";

export default function GeneratingStep() {
  return (
    <div className="flex min-h-[75vh] flex-col items-center justify-center text-center">

      <Sparkles
        className="mb-6 text-purple-600"
        size={60}
      />

      <Loader2
        className="animate-spin text-purple-600"
        size={48}
      />

      <h1 className="mt-8 text-3xl font-bold">
        Creating your AI roadmap
      </h1>

      <p className="mt-4 max-w-lg text-muted-foreground">
        We're analyzing your goals, experience,
        learning style and available study time.
      </p>

      <div className="mt-12 w-full max-w-md">

        <div className="mb-5 h-2 overflow-hidden rounded-full bg-gray-200">
          <div className="h-full w-3/4 animate-pulse rounded-full bg-purple-600" />
        </div>

        <ul className="space-y-3 text-left text-sm">

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