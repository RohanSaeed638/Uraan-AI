"use client";

import { useQuery } from "@tanstack/react-query";

import { getAchievements } from "@/lib/api/achievements";

import BossCard from "@/components/achievements/BossCard";
import ReadinessCard from "@/components/achievements/ReadinessCard";

/** Career readiness and this month's boss project, on the dashboard. */
export default function ProgressRow() {
  const query = useQuery({
    queryKey: ["achievements"],
    queryFn: getAchievements,
    staleTime: 30_000,
    retry: false,
  });

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <ReadinessCard compact />
      {query.data && <BossCard boss={query.data.boss} />}
    </div>
  );
}
