"use client";

import { useQuery } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";

import { getMotivation } from "@/lib/api/mentor";

import { Card } from "@/components/ui/card";

/** Today's short message, written from the learner's real progress. Shows
 * nothing while loading or if it cannot be loaded: it is a nicety, not a
 * dependency. */
export default function MotivationCard() {
  const query = useQuery({
    queryKey: ["mentor", "motivation"],
    queryFn: getMotivation,
    staleTime: 60 * 60 * 1000,
    retry: false,
  });

  if (!query.data?.message) return null;

  return (
    <Card className="flex-row items-start gap-3 border-brand-violet/30 bg-brand-violet/5 px-5 py-4">
      <Sparkles size={18} className="mt-0.5 shrink-0 text-brand-violet" />
      <p className="min-w-0 break-words text-sm leading-6">{query.data.message}</p>
    </Card>
  );
}
