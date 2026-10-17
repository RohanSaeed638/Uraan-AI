"use client";

import Link from "next/link";
import { Clock, ArrowRight } from "lucide-react";

import { RoadmapSummary } from "@/types/roadmap";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { Progress } from "@/components/ui/progress";
import { buttonVariants } from "@/components/ui/button";

interface Props {
  roadmap: RoadmapSummary;
}

const statusStyles: Record<string, string> = {
  active: "bg-emerald-500/15 text-emerald-500",
  completed: "bg-brand-violet/15 text-brand-violet",
  paused: "bg-muted text-muted-foreground",
};

export default function RoadmapCard({ roadmap }: Props) {
  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="line-clamp-1">{roadmap.title}</CardTitle>
          <span
            className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium capitalize ${
              statusStyles[roadmap.status] ?? "bg-muted text-muted-foreground"
            }`}
          >
            {roadmap.status}
          </span>
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        <p className="line-clamp-2 text-sm text-muted-foreground">
          {roadmap.description}
        </p>

        <Progress value={roadmap.progress} />

        <div className="flex justify-between text-sm text-muted-foreground">
          <span>
            {roadmap.completed_tasks} / {roadmap.total_tasks} Tasks
          </span>
          <span>{roadmap.progress}%</span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock size={14} />
            Updated {new Date(roadmap.updated_at).toLocaleDateString()}
          </div>

          <Link
            href={`/roadmaps/${roadmap.id}`}
            className={buttonVariants({ className: "gap-1.5" })}
          >
            Continue <ArrowRight size={15} />
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
