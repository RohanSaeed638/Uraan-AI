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
import { Button } from "@/components/ui/button";

interface Props {
  roadmap: RoadmapSummary;
}

export default function RoadmapCard({
  roadmap,
}: Props) {
  return (
    <Card>
      <CardHeader>

        <div className="flex items-center justify-between">

          <CardTitle>
            {roadmap.title}
          </CardTitle>

          <span
            className="
              rounded-full
              bg-primary/10
              px-3
              py-1
              text-xs
              font-medium
              text-primary
            "
          >
            {roadmap.status}
          </span>

        </div>

      </CardHeader>

      <CardContent className="space-y-5">

        <p className="text-sm text-muted-foreground">
          {roadmap.description}
        </p>

        <Progress value={roadmap.progress} />

        <div className="flex justify-between text-sm text-muted-foreground">
          <span>
            {roadmap.completed_tasks} / {roadmap.total_tasks} Tasks
          </span>

          <span>
            {roadmap.progress}%
          </span>
        </div>

        <div className="flex items-center justify-between">

          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock size={16} />
            Updated{" "}
            {new Date(
              roadmap.updated_at
            ).toLocaleDateString()}
          </div>

          <Button>

            <Link
              href={`/roadmaps/${roadmap.id}`}
              className="flex items-center gap-2"
            >
              <span>Continue </span>
              <ArrowRight className="ml-2 h-4 w-4"/>
            </Link>

          </Button>

        </div>

      </CardContent>
    </Card>
  );
}