"use client";

import { useState } from "react";
import {
  Clock,
  BookOpen,
} from "lucide-react";

import TaskList from "./TaskList";

import { Roadmap } from "@/types/roadmap";

interface RoadmapDetailClientProps {
  roadmap: Roadmap;
}

export default function RoadmapDetailClient({
  roadmap: initialRoadmap,
}: RoadmapDetailClientProps) {
  const [roadmap, setRoadmap] =
    useState<Roadmap>(initialRoadmap);

  function calculateProgress(roadmap: Roadmap) {
    const tasks = roadmap.phases.flatMap(
      (phase) => phase.tasks
    );

    if (tasks.length === 0) {
      return 0;
    }

    const completed = tasks.filter(
      (task) => task.completed
    ).length;

    return Math.round(
      (completed / tasks.length) * 100
    );
  }

  const progress = calculateProgress(roadmap);

  const totalHours = roadmap.phases
    .flatMap((phase) => phase.tasks)
    .reduce(
      (total, task) =>
        total + (task.estimated_hours ?? 0),
      0
    );

  function handleRoadmapChange(
    updatedRoadmap: Roadmap
  ) {
    setRoadmap(updatedRoadmap);
  }

  return (
    <div className="mx-auto max-w-5xl">
      {/* Header */}
      <section className="rounded-xl border bg-card p-8">
        <div className="flex items-start justify-between gap-5">
          <div className="min-w-0">
            <h1 className="text-3xl font-bold">
              {roadmap.title}
            </h1>

            <p className="mt-4 leading-7 text-muted-foreground">
              {roadmap.description}
            </p>
          </div>

          <span
            className="
              shrink-0
              rounded-full
              bg-green-100
              px-4
              py-2
              text-sm
              font-medium
              text-green-700
            "
          >
            {roadmap.status}
          </span>
        </div>

        {/* Stats */}
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border p-4">
            <p className="text-sm text-muted-foreground">
              Completion
            </p>

            <p className="mt-2 text-2xl font-bold">
              {progress}%
            </p>
          </div>

          <div className="rounded-lg border p-4">
            <p className="text-sm text-muted-foreground">
              Total Learning Hours
            </p>

            <p className="mt-2 flex items-center gap-2 text-2xl font-bold">
              <Clock size={22} />
              {totalHours}h
            </p>
          </div>

          <div className="rounded-lg border p-4">
            <p className="text-sm text-muted-foreground">
              Phases
            </p>

            <p className="mt-2 flex items-center gap-2 text-2xl font-bold">
              <BookOpen size={22} />
              {roadmap.phases.length}
            </p>
          </div>
        </div>

        {/* Overall Progress */}
        <div className="mt-8">
          <div className="mb-2 flex justify-between text-sm">
            <span>Overall progress</span>

            <span>{progress}%</span>
          </div>

          <div className="h-3 overflow-hidden rounded-full bg-muted">
            <div
              className="
                h-full
                rounded-full
                bg-primary
                transition-all
                duration-300
              "
              style={{
                width: `${progress}%`,
              }}
            />
          </div>
        </div>
      </section>

      {/* Tasks */}
      <TaskList
        roadmap={roadmap}
        onRoadmapChange={handleRoadmapChange}
      />
    </div>
  );
}