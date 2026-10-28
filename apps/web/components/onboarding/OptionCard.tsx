"use client";

import { ReactNode } from "react";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface OptionCardProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  selected: boolean;
  onClick: () => void;
}

export default function OptionCard({
  title,
  description,
  icon,
  selected,
  onClick,
}: OptionCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "relative w-full rounded-2xl border p-5 text-start transition-all",
        "hover:-translate-y-0.5 hover:border-brand-gold/50 hover:shadow-md",
        selected
          ? "border-brand-gold bg-brand-gold/10 ring-2 ring-brand-gold/40"
          : "border-border bg-card"
      )}
    >
      {selected && (
        <span className="absolute end-4 top-4 flex size-5 items-center justify-center rounded-full bg-brand-gold text-[#241a05]">
          <Check size={12} strokeWidth={3} />
        </span>
      )}

      {icon && (
        <div
          className={cn(
            "mb-4 flex size-10 items-center justify-center rounded-xl",
            selected
              ? "bg-brand-violet text-white"
              : "bg-brand-gold/15 text-brand-gold-deep dark:text-brand-gold"
          )}
        >
          {icon}
        </div>
      )}

      <h3 className="pe-6 font-semibold">{title}</h3>

      {description && (
        <p className="mt-1.5 text-sm text-muted-foreground">{description}</p>
      )}
    </button>
  );
}
