import { LucideIcon } from "lucide-react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

/** Shown instead of a list with nothing in it: says what is missing and what
 * to do about it. */
export default function EmptyState({
  icon: Icon,
  title,
  text,
  action,
  className,
}: {
  icon: LucideIcon;
  title: string;
  text?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <Card className={cn("items-center gap-3 border-dashed p-10 text-center", className)}>
      <span className="flex size-14 items-center justify-center rounded-full bg-brand-gold/15 text-brand-gold">
        <Icon size={26} />
      </span>
      <p className="font-heading text-lg font-semibold">{title}</p>
      {text && <p className="max-w-md text-sm text-muted-foreground">{text}</p>}
      {action && <div className="mt-1">{action}</div>}
    </Card>
  );
}
