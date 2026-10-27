import { LucideIcon } from "lucide-react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const TONES = {
  gold: "bg-brand-gold/15 text-brand-gold",
  violet: "bg-brand-violet/15 text-brand-violet-light",
  green: "bg-emerald-500/15 text-emerald-500",
  sky: "bg-sky-500/15 text-sky-500",
} as const;

/** One number with an icon and a label: totals, streaks, counts. */
export default function StatTile({
  icon: Icon,
  value,
  label,
  tone = "gold",
  className,
}: {
  icon: LucideIcon;
  value: React.ReactNode;
  label: string;
  tone?: keyof typeof TONES;
  className?: string;
}) {
  return (
    <Card className={cn("flex-row items-center gap-3 p-4", className)}>
      <span
        className={cn(
          "flex size-10 shrink-0 items-center justify-center rounded-xl",
          TONES[tone]
        )}
      >
        <Icon size={18} />
      </span>
      <div className="min-w-0">
        <p className="font-heading text-xl font-bold leading-none">{value}</p>
        <p className="mt-1 truncate text-xs text-muted-foreground">{label}</p>
      </div>
    </Card>
  );
}
