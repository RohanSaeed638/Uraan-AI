"use client";

import { useState } from "react";

interface RoadmapProgressProps {
  initialProgress: number;
  children: (
    progress: number,
    onProgressChange: (
      progress: number
    ) => void
  ) => React.ReactNode;
}

export default function RoadmapProgress({
  initialProgress,
  children,
}: RoadmapProgressProps) {
  const [progress, setProgress] =
    useState(initialProgress);

  return (
    <>
      {children(progress, setProgress)}
    </>
  );
}