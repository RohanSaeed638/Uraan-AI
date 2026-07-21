"use client";

import { Loader2 } from "lucide-react";

export default function LoadingAnimation() {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <Loader2 className="h-12 w-12 animate-spin text-purple-600" />

      <h2 className="mt-8 text-2xl font-semibold">
        Creating your roadmap...
      </h2>

      <p className="mt-3 text-gray-500">
        Our AI is preparing your personalized learning plan.
      </p>
    </div>
  );
}