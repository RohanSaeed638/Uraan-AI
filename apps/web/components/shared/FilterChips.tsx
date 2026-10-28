"use client";

import Link from "next/link";

import { cn } from "@/lib/utils";

export interface ChipOption<T extends string> {
  value: T;
  label: string;
  /** A number shown after the label, e.g. how many items match. */
  count?: number;
  /** Makes the chip a link instead of a button (for URL-driven filters). */
  href?: string;
}

interface Props<T extends string> {
  options: ChipOption<T>[];
  value: T;
  onChange?: (value: T) => void;
  /** Names the group for screen readers, e.g. "Difficulty". */
  label: string;
  /** "segmented" joins the chips into one control (view switchers). */
  variant?: "chips" | "segmented";
  size?: "sm" | "md";
  className?: string;
}

/** A single choice from a few: the app's filter buttons and tabs. The chosen
 * one is gold. */
export default function FilterChips<T extends string>({
  options,
  value,
  onChange,
  label,
  variant = "chips",
  size = "md",
  className,
}: Props<T>) {
  const segmented = variant === "segmented";

  return (
    <div
      role="group"
      aria-label={label}
      className={cn(
        "flex gap-2",
        segmented
          ? "inline-flex gap-0 rounded-full border border-border bg-muted/50 p-1"
          : "flex-wrap",
        className
      )}
    >
      {options.map((option) => {
        const active = option.value === value;
        const classes = cn(
          "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full font-medium transition",
          "outline-none focus-visible:ring-3 focus-visible:ring-ring/40",
          size === "sm" ? "px-3 py-1 text-xs" : "px-4 py-1.5 text-sm",
          active
            ? "bg-brand-gold text-[#241a05] shadow-sm"
            : segmented
              ? "text-muted-foreground hover:text-foreground"
              : "border border-border bg-card text-muted-foreground hover:border-brand-gold/60 hover:bg-brand-gold/10 hover:text-foreground"
        );
        const content = (
          <>
            {option.label}
            {option.count !== undefined && (
              <span
                className={cn(
                  "rounded-full px-1.5 text-[11px] leading-5",
                  active ? "bg-black/10" : "bg-muted text-muted-foreground"
                )}
              >
                {option.count}
              </span>
            )}
          </>
        );

        if (option.href) {
          return (
            <Link
              key={option.value}
              href={option.href}
              aria-current={active ? "page" : undefined}
              className={classes}
            >
              {content}
            </Link>
          );
        }

        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={active}
            onClick={() => onChange?.(option.value)}
            className={classes}
          >
            {content}
          </button>
        );
      })}
    </div>
  );
}
