import { notFound } from "next/navigation";
import {
  Clock,
  BookOpen
} from "lucide-react";
import { createClient } from "@/lib/supabase/server";

import TaskList from "./TaskList";
import { RoadmapPhase } from "@/types/roadmap";


export default async function RoadmapDetailPage({
  params,
}: {
  params: Promise<{
    id: string;
  }>;
}) {

  const supabase = await createClient();

  async function authHeader() {
    const {
      data: { session },
    } = await supabase.auth.getSession();

   return {
      Authorization: `Bearer ${session?.access_token}`,
    };
  }

  async function getRoadmap(id: string) {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/roadmaps/${id}`,
      {
        headers: await authHeader(),
        cache: "no-store",
        credentials: "include",
      }
    );

    if (!response.ok) {
      return null;
    }

    return response.json();
  }


  function calculateProgress(phases: RoadmapPhase[]) {
    const tasks = phases.flatMap((phase) => phase.tasks);

    const completed = tasks.filter(
      (task) => task.completed
    ).length;

    return Math.round(
      (completed / tasks.length) * 100
    );
  }


  const { id } = await params;

  const roadmap = await getRoadmap(id);

  
  if (!roadmap) {
    notFound();
  }

  const progress = calculateProgress(
    roadmap.phases
  );


  const totalHours =
    roadmap.phases
      .flatMap((phase:any)=>phase.tasks)
      .reduce(
        (
          total:number,
          task:any
        ) =>
          total + task.estimated_hours,
        0
      );


  return (
    <main className="min-h-screen bg-background px-6 py-10">

      <div className="mx-auto max-w-5xl">


        {/* Header */}
        <section className="rounded-xl border bg-card p-8">

          <div className="flex items-start justify-between gap-5">

            <div>

              <h1 className="text-3xl font-bold">
                {roadmap.title}
              </h1>


              <p className="mt-4 text-muted-foreground leading-7">
                {roadmap.description}
              </p>

            </div>


            <span
              className="
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

                <Clock size={22}/>

                {totalHours}h

              </p>

            </div>



            <div className="rounded-lg border p-4">

              <p className="text-sm text-muted-foreground">
                Phases
              </p>

              <p className="mt-2 flex items-center gap-2 text-2xl font-bold">

                <BookOpen size={22}/>

                {roadmap.phases.length}

              </p>

            </div>


          </div>



          {/* Progress bar */}

          <div className="mt-8">

            <div className="mb-2 flex justify-between text-sm">

              <span>
                Overall progress
              </span>

              <span>
                {progress}%
              </span>

            </div>


            <div
              className="
              h-3 
              overflow-hidden 
              rounded-full 
              bg-muted
              "
            >

              <div
                className="
                h-full
                bg-primary
                transition-all
                "
                style={{
                  width:`${progress}%`
                }}
              />

            </div>


          </div>


        </section>



        {/* Phases */}

        <TaskList roadmap={roadmap}/>

      </div>

    </main>
  );
}