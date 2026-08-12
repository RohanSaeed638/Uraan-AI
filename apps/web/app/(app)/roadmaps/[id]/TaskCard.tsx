// "use client";

// import {
//   Clock,
//   ExternalLink,
//   Loader2,
// } from "lucide-react";

// import { Checkbox } from "@/components/ui/checkbox";
// import {
//   Card,
//   CardContent,
// } from "@/components/ui/card";

// import { RoadmapTask } from "@/types/roadmap";

// interface TaskCardProps {
//   task: RoadmapTask;
//   loading?: boolean;
//   onToggle: (
//     taskId: string,
//     completed: boolean
//   ) => void;
// }

// export function TaskCard({
//   task,
//   loading = false,
//   onToggle,
// }: TaskCardProps) {
//   return (
//     <Card
//       className={
//         task.completed
//           ? "opacity-70 transition-all"
//           : "transition-all"
//       }
//     >
//       <CardContent className="flex gap-4 p-5">
//         <div className="pt-1">
//           {loading ? (
//             <Loader2
//               className="
//                 h-5
//                 w-5
//                 animate-spin
//                 text-muted-foreground
//               "
//             />
//           ) : (
//             <Checkbox
//               checked={task.completed}
//               disabled={loading}
//               onCheckedChange={(checked) => {
//                 onToggle(
//                   task.id,
//                   checked === true
//                 );
//               }}
//             />
//           )}
//         </div>

//         <div className="flex-1 space-y-2">
//           <div className="flex items-start justify-between gap-4">
//             <h4
//               className={`
//                 font-medium
//                 transition-all
//                 ${
//                   task.completed
//                     ? "text-muted-foreground line-through"
//                     : ""
//                 }
//               `}
//             >
//               {task.title}
//             </h4>

//             {task.estimated_hours != null && (
//               <div
//                 className="
//                   flex
//                   shrink-0
//                   items-center
//                   gap-1
//                   whitespace-nowrap
//                   text-sm
//                   text-muted-foreground
//                 "
//               >
//                 <Clock className="h-4 w-4" />

//                 {task.estimated_hours} hrs
//               </div>
//             )}
//           </div>

//           {task.description && (
//             <p className="text-sm leading-6 text-muted-foreground">
//               {task.description}
//             </p>
//           )}

//           {task.resource_url && (
//             <a
//               href={task.resource_url}
//               target="_blank"
//               rel="noopener noreferrer"
//               className="
//                 inline-flex
//                 items-center
//                 gap-1
//                 text-sm
//                 text-primary
//                 hover:underline
//               "
//             >
//               Open resource

//               <ExternalLink className="h-3 w-3" />
//             </a>
//           )}
//         </div>
//       </CardContent>
//     </Card>
//   );
// }

"use client";

import {
  Clock,
  ExternalLink,
  Loader2,
} from "lucide-react";

import { Checkbox } from "@/components/ui/checkbox";

import {
  Card,
  CardContent,
} from "@/components/ui/card";

import { RoadmapTask } from "@/types/roadmap";

interface TaskCardProps {
  task: RoadmapTask;
  loading?: boolean;

  onToggle: (
    taskId: string,
    completed: boolean
  ) => void;

  onOpen: (task: RoadmapTask) => void;
}

export function TaskCard({
  task,
  loading = false,
  onToggle,
  onOpen,
}: TaskCardProps) {
  return (
    <Card
      onClick={() => onOpen(task)}
      className={`
        cursor-pointer
        transition-all
        hover:border-primary/50
        hover:shadow-sm
        ${
          task.completed
            ? "opacity-70"
            : ""
        }
      `}
    >
      <CardContent className="flex gap-4 p-5">
        {/* Checkbox */}
        <div
          className="pt-1"
          onClick={(event) =>
            event.stopPropagation()
          }
        >
          {loading ? (
            <Loader2
              className="
                h-5
                w-5
                animate-spin
                text-muted-foreground
              "
            />
          ) : (
            <Checkbox
              checked={task.completed}
              disabled={loading}
              onCheckedChange={(checked) => {
                onToggle(
                  task.id,
                  checked === true
                );
              }}
            />
          )}
        </div>

        {/* Task content */}
        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex items-start justify-between gap-4">
            <h4
              className={`
                font-medium
                transition-all
                ${
                  task.completed
                    ? "text-muted-foreground line-through"
                    : ""
                }
              `}
            >
              {task.title}
            </h4>

            {task.estimated_hours != null && (
              <div
                className="
                  flex
                  shrink-0
                  items-center
                  gap-1
                  whitespace-nowrap
                  text-sm
                  text-muted-foreground
                "
              >
                <Clock className="h-4 w-4" />

                {task.estimated_hours} hrs
              </div>
            )}
          </div>

          {task.description && (
            <p className="text-sm leading-6 text-muted-foreground">
              {task.description}
            </p>
          )}

          {task.resource_url && (
            <a
              href={task.resource_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(event) =>
                event.stopPropagation()
              }
              className="
                inline-flex
                items-center
                gap-1
                text-sm
                text-primary
                hover:underline
              "
            >
              Open resource

              <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
      </CardContent>
    </Card>
  );
}