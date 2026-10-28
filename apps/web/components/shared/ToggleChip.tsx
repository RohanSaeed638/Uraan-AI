"use client";

import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

/** An on/off filter (Free only, Saved only...). Gold with a tick when on. */
export default function ToggleChip({
  checked,
  onChange,
  children,
  className,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={cn(
        "inline-flex items-center gap-2 whitespace-nowrap rounded-full border px-4 py-1.5 text-sm font-medium transition",
        "outline-none focus-visible:ring-3 focus-visible:ring-ring/40",
        checked
          ? "border-brand-gold bg-brand-gold/15 text-foreground"
          : "border-border bg-card text-muted-foreground hover:border-brand-gold/60 hover:bg-brand-gold/10 hover:text-foreground",
        className
      )}
    >
      <span
        aria-hidden
        className={cn(
          "flex size-4 items-center justify-center rounded-full border transition",
          checked
            ? "border-brand-gold bg-brand-gold text-[#241a05]"
            : "border-muted-foreground/50"
        )}
      >
        {checked && <Check size={11} strokeWidth={3.5} />}
      </span>
      {children}
    </button>
  );
}
