import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * A plain browser select styled like our inputs. Native on purpose: it works
 * with the keyboard and screen readers, and on phones it uses the system
 * picker, which beats a custom dropdown for long lists such as timezones.
 */
export default function NativeSelect({
  className,
  children,
  active,
  ...props
}: React.ComponentProps<"select"> & {
  /** Marks the filter as set (not at its default): gold outline. */
  active?: boolean;
}) {
  return (
    <select
      className={cn(
        "h-9 w-full min-w-0 rounded-3xl border bg-input/50 px-3 text-base outline-none transition-[color,box-shadow,background-color] focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        active ? "border-brand-gold/70 bg-brand-gold/10" : "border-transparent",
        className
      )}
      {...props}
    >
      {children}
    </select>
  );
}
