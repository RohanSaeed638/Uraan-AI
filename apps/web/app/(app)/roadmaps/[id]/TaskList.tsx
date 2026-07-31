"use client";
import {
  ChevronDown
} from "lucide-react";
import { TaskCard } from "./TaskCard";
import { api } from "@/lib/api/client";
import { Roadmap, RoadmapPhase, RoadmapTask } from "@/types/roadmap";
import { useState, useEffect } from "react";

export default function TaskList({ roadmap:roadmapProp }: { roadmap: Roadmap }) {
      const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
      
      useEffect(() => {
        setRoadmap(roadmapProp);
        }, [roadmap]);

      const updateTask = async (taskId: string, completed: boolean) => {
        await api.patch(`/roadmaps/tasks/${taskId}`, {
            completed,
        });
    
        setRoadmap((prev:Roadmap | null) => {
            if (!prev) return null;
            return {
                ...prev,
                phases: prev.phases.map((phase:RoadmapPhase) => ({
                    ...phase,
                    tasks: phase.tasks.map((task: RoadmapTask) =>
                        task.id === taskId
                        ? { ...task, completed }
                        : task
                ),
            })),
        }});
    };
    if (!roadmap) {
        return <div>Loading...</div>;
    }
    return (
        <>
        <section className="mt-10 space-y-5">


          {
            roadmap.phases.map(
              (
                phase:any
              ) => (

              <details
                key={phase.id}
                className="
                group
                rounded-xl
                border
                bg-card
                "
              >


                <summary
                  className="
                  flex
                  cursor-pointer
                  list-none
                  items-center
                  justify-between
                  p-6
                  "
                >

                  <div>

                    <h2 className="text-xl font-semibold">

                      {phase.title}

                    </h2>


                    <p className="mt-2 text-sm text-muted-foreground">

                      {phase.description}

                    </p>

                  </div>
                  <ChevronDown
                    className="
                    transition-transform
                    group-open:rotate-180
                    "
                  />


                </summary>



                <div className="border-t p-6">


                  <div className="space-y-4">


                  {
                    phase.tasks.map(
                      (
                        task:any
                      ) => (
                    <TaskCard
                        key={task.id}
                        task={task}
                        onToggle={updateTask}
                    />
                    )
                    )
                  }


                  </div>


                </div>


              </details>

            ))
          }


        </section>
        </>
    );
}