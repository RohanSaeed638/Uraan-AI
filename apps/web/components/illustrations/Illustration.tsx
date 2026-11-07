import Image from "next/image";

import { cn } from "@/lib/utils";

/** The pictures in `public/illustrations`. Each has a light and a dark version. */
export type IllustrationName =
  | "hero" | "bird" | "path" | "signpost" | "guide" | "study" | "focus" | "steps"
  | "certificate" | "trophy" | "flame" | "milestone" | "empty" | "search" | "bell"
  | "offline" | "chart" | "chat" | "crown" | "success"
  | "ob-goal" | "ob-plan" | "ob-ai" | "ob-skills" | "ob-mentor" | "ob-journey" | "ob-continue" | "ob-done"
  | "dashboard" | "roadmaps" | "explore" | "learning" | "tasks" | "projects"
  | "progress" | "achievement" | "mentor" | "profile" | "settings";

/**
 * A decorative picture that follows the theme. The light version has an off-white backdrop, which
 * `mix-blend-multiply` makes disappear against a white page or card; the dark version has its
 * background removed. Decorative only: screen readers skip it.
 */
export default function Illustration({
  name,
  size = 160,
  className,
  priority = false,
}: {
  name: IllustrationName;
  size?: number;
  className?: string;
  priority?: boolean;
}) {
  const common = { fill: true, sizes: `${size}px`, priority, "aria-hidden": true, draggable: false } as const;

  return (
    <div className={cn("relative shrink-0 select-none", className)} style={{ width: size, height: size }} aria-hidden>
      <Image
        {...common}
        alt=""
        src={`/illustrations/${name}.light.webp`}
        className="object-contain mix-blend-multiply dark:hidden"
      />
      <Image {...common} alt="" src={`/illustrations/${name}.dark.webp`} className="hidden object-contain dark:block" />
    </div>
  );
}
