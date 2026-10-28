import { cn } from "@/lib/utils";

/** A small rounded label, e.g. a difficulty or demand level. */
export default function Pill({
  children,
  tone = "outline",
  className,
}: {
  children: React.ReactNode;
  tone?: "outline" | "soft" | "gold";
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        tone === "outline"
          ? "border border-border text-foreground/80"
          : tone === "gold"
            ? "bg-brand-gold/20 text-brand-gold-deep dark:text-brand-gold-light"
            : "bg-brand-violet/15 text-brand-violet",
        className
      )}
    >
      {children}
    </span>
  );
}
