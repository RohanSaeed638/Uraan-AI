// "use client";

// import {
//   Clock,
//   ExternalLink,
//   CheckCircle2,
// } from "lucide-react";

// import {
//   Dialog,
//   DialogContent,
//   DialogDescription,
//   DialogHeader,
//   DialogTitle,
// } from "@/components/ui/dialog";

// import { Button } from "@/components/ui/button";

// import { RoadmapTask } from "@/types/roadmap";

// interface TaskDetailsDialogProps {
//   task: RoadmapTask | null;
//   open: boolean;
//   onOpenChange: (open: boolean) => void;

//   onToggle: (
//     taskId: string,
//     completed: boolean
//   ) => void;
// }

// export default function TaskDetailsDialog({
//   task,
//   open,
//   onOpenChange,
//   onToggle,
// }: TaskDetailsDialogProps) {
//   if (!task) {
//     return null;
//   }

//   return (
//     <Dialog
//       open={open}
//       onOpenChange={onOpenChange}
//     >
//       <DialogContent className="sm:max-w-lg">
//         <DialogHeader>
//           <DialogTitle className="text-xl">
//             {task.title}
//           </DialogTitle>

//           <DialogDescription>
//             Task details and learning resources.
//           </DialogDescription>
//         </DialogHeader>

//         <div className="space-y-6">
//           {/* Description */}
//           {task.description && (
//             <div>
//               <h3 className="mb-2 text-sm font-semibold">
//                 What you need to do
//               </h3>

//               <p className="text-sm leading-6 text-muted-foreground">
//                 {task.description}
//               </p>
//             </div>
//           )}

//           {/* Estimated time */}
//           {task.estimated_hours != null && (
//             <div className="flex items-center gap-3 rounded-lg border p-4">
//               <Clock className="h-5 w-5 text-muted-foreground" />

//               <div>
//                 <p className="text-sm font-medium">
//                   Estimated time
//                 </p>

//                 <p className="text-sm text-muted-foreground">
//                   {task.estimated_hours} hours
//                 </p>
//               </div>
//             </div>
//           )}

//           {/* Resource */}
//           {task.resource_url && (
//             <div>
//               <h3 className="mb-2 text-sm font-semibold">
//                 Learning resource
//               </h3>

//               <a
//                 href={task.resource_url}
//                 target="_blank"
//                 rel="noopener noreferrer"
//                 className="
//                   inline-flex
//                   items-center
//                   gap-2
//                   text-sm
//                   text-primary
//                   hover:underline
//                 "
//               >
//                 Open learning resource

//                 <ExternalLink className="h-4 w-4" />
//               </a>
//             </div>
//           )}

//           {/* Completion */}
//           <div className="border-t pt-5">
//             {task.completed ? (
//               <Button
//                 variant="outline"
//                 className="w-full"
//                 onClick={() =>
//                   onToggle(task.id, false)
//                 }
//               >
//                 <CheckCircle2 className="mr-2 h-4 w-4" />

//                 Mark as incomplete
//               </Button>
//             ) : (
//               <Button
//                 className="w-full"
//                 onClick={() =>
//                   onToggle(task.id, true)
//                 }
//               >
//                 Mark as complete
//               </Button>
//             )}
//           </div>
//         </div>
//       </DialogContent>
//     </Dialog>
//   );
// }


"use client";

import {
  Clock,
  ExternalLink,
  CheckCircle2,
  BookOpen,
} from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import { Button } from "@/components/ui/button";

import { RoadmapTask } from "@/types/roadmap";

interface TaskDetailsDialogProps {
  task: RoadmapTask | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;

  onToggle: (
    taskId: string,
    completed: boolean
  ) => void;
}

export default function TaskDetailsDialog({
  task,
  open,
  onOpenChange,
  onToggle,
}: TaskDetailsDialogProps) {
  if (!task) {
    return null;
  }

  const hasResources =
    task.resource_links &&
    task.resource_links.length > 0;

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {task.title}
          </DialogTitle>

          <DialogDescription>
            Task details and learning resources.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Description */}
          {task.description && (
            <div>
              <h3 className="mb-2 text-sm font-semibold">
                What you need to do
              </h3>

              <p className="text-sm leading-6 text-muted-foreground">
                {task.description}
              </p>
            </div>
          )}

          {/* Estimated time */}
          {task.estimated_hours != null && (
            <div className="flex items-center gap-3 rounded-lg border p-4">
              <Clock className="h-5 w-5 text-muted-foreground" />

              <div>
                <p className="text-sm font-medium">
                  Estimated time
                </p>

                <p className="text-sm text-muted-foreground">
                  {task.estimated_hours}{" "}
                  {task.estimated_hours === 1
                    ? "hour"
                    : "hours"}
                </p>
              </div>
            </div>
          )}

          {/* Learning Resources */}
          {hasResources && (
            <div>
              <div className="mb-3 flex items-center gap-2">
                <BookOpen className="h-4 w-4" />

                <h3 className="text-sm font-semibold">
                  Learning resources
                </h3>
              </div>

              <div className="space-y-2">
                {task.resource_links!.map(
                  (url, index) => (
                    <a
                      key={`${url}-${index}`}
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="
                        flex
                        items-center
                        justify-between
                        gap-3
                        rounded-lg
                        border
                        p-3
                        text-sm
                        transition-colors
                        hover:bg-muted
                      "
                    >
                      <span className="min-w-0 truncate text-primary">
                        Resource {index + 1}
                      </span>

                      <ExternalLink className="h-4 w-4 shrink-0 text-muted-foreground" />
                    </a>
                  )
                )}
              </div>
            </div>
          )}

          {/* No resources */}
          {!hasResources && (
            <div className="rounded-lg border border-dashed p-4">
              <p className="text-sm text-muted-foreground">
                No learning resources are available
                for this task yet.
              </p>
            </div>
          )}

          {/* Completion */}
          <div className="border-t pt-5">
            {task.completed ? (
              <Button
                variant="outline"
                className="w-full"
                onClick={() =>
                  onToggle(task.id, false)
                }
              >
                <CheckCircle2 className="mr-2 h-4 w-4" />

                Mark as incomplete
              </Button>
            ) : (
              <Button
                className="w-full"
                onClick={() =>
                  onToggle(task.id, true)
                }
              >
                Mark as complete
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}