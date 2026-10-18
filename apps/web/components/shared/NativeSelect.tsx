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
  ...props
}: React.ComponentProps<"select">) {
  return (
    <select
      className={cn(
        "h-9 w-full min-w-0 rounded-3xl border border-transparent bg-input/50 px-3 text-base outline-none transition-[color,box-shadow,background-color] focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        className
      )}
      {...props}
    >
      {children}
    </select>
  );
}
