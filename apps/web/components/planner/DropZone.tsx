"use client";

import { useState } from "react";

import { cn } from "@/lib/utils";

/** A day that lessons can be dropped on. Today and later accept drops; past
 * days do not. Lights up gold while a lesson is over it. */
export default function DropZone({
  date,
  today,
  onDropLesson,
  className,
  children,
}: {
  date: string;
  today: string;
  onDropLesson: (lessonId: string, date: string) => void;
  className?: string;
  children: React.ReactNode;
}) {
  const [over, setOver] = useState(false);
  const allowed = date >= today;

  return (
    <div
      className={cn(className, over && allowed && "ring-2 ring-brand-gold/70 ring-offset-0")}
      onDragOver={(e) => {
        if (!allowed) return;

        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        setOver(false);

        if (!allowed) return;

        e.preventDefault();

        const id = e.dataTransfer.getData("text/plain");

        if (id) onDropLesson(id, date);
      }}
    >
      {children}
    </div>
  );
}
