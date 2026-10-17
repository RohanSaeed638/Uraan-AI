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
        "relative w-full rounded-2xl border p-5 text-left transition-all",
        "hover:-translate-y-0.5 hover:shadow-md",
        selected
          ? "border-brand-violet bg-brand-violet/10 ring-2 ring-brand-violet/40"
          : "border-border bg-card"
      )}
    >
      {selected && (
        <span className="absolute right-4 top-4 flex size-5 items-center justify-center rounded-full bg-brand-violet text-white">
          <Check size={12} strokeWidth={3} />
        </span>
      )}

      {icon && (
        <div
          className={cn(
            "mb-4 flex size-10 items-center justify-center rounded-xl",
            selected
              ? "bg-brand-violet text-white"
              : "bg-brand-violet/10 text-brand-violet"
          )}
        >
          {icon}
        </div>
      )}

      <h3 className="pr-6 font-semibold">{title}</h3>

      {description && (
        <p className="mt-1.5 text-sm text-muted-foreground">{description}</p>
      )}
    </button>
  );
}
