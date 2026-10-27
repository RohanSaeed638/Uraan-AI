"use client";

import { useTranslations } from "next-intl";
import { Search, X } from "lucide-react";

import { cn } from "@/lib/utils";

/** A search box with an icon and a clear button. Gold when it has a value. */
export default function SearchField({
  value,
  onChange,
  placeholder,
  label,
  className,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  label?: string;
  className?: string;
}) {
  const tShared = useTranslations("shared");

  return (
    <div className={cn("relative", className)}>
      <Search
        size={16}
        aria-hidden
        className={cn(
          "pointer-events-none absolute start-3.5 top-1/2 -translate-y-1/2 transition-colors",
          value ? "text-brand-gold" : "text-muted-foreground"
        )}
      />
      <input
        type="search"
        aria-label={label ?? placeholder}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          "h-10 w-full rounded-full border bg-input/50 ps-10 pe-10 text-sm outline-none transition",
          "placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30",
          "[&::-webkit-search-cancel-button]:hidden",
          value ? "border-brand-gold/60" : "border-transparent"
        )}
      />
      {value && (
        <button
          type="button"
          aria-label={tShared("clearSearch")}
          onClick={() => onChange("")}
          className="absolute end-2.5 top-1/2 flex size-6 -translate-y-1/2 items-center justify-center rounded-full text-muted-foreground transition hover:bg-muted hover:text-foreground"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}
