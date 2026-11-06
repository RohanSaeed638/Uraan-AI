import { LucideIcon } from "lucide-react";

import Illustration, { IllustrationName } from "@/components/illustrations/Illustration";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

/** Shown instead of a list with nothing in it: says what is missing and what
 * to do about it. */
export default function EmptyState({
  icon: Icon,
  art,
  title,
  text,
  action,
  className,
}: {
  icon?: LucideIcon;
  /** A picture shown in place of the icon. */
  art?: IllustrationName;
  title: string;
  text?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <Card className={cn("items-center gap-3 border-dashed p-10 text-center", className)}>
      {art ? (
        <Illustration name={art} size={150} />
      ) : (
        Icon && (
          <span className="flex size-14 items-center justify-center rounded-full bg-brand-violet/15 text-violet-600 dark:text-brand-violet-light">
            <Icon size={26} />
          </span>
        )
      )}
      <p className="font-heading text-lg font-semibold">{title}</p>
      {text && <p className="max-w-md text-sm text-muted-foreground">{text}</p>}
      {action && <div className="mt-1">{action}</div>}
    </Card>
  );
}
