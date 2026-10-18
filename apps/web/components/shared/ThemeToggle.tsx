"use client";

import { Monitor, Moon, Sun } from "lucide-react";

import { api } from "@/lib/api";
import { setStoredTheme, Theme, useTheme } from "@/lib/theme";
import { cn } from "@/lib/utils";

const OPTIONS: { value: Theme; label: string; icon: typeof Sun }[] = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Monitor },
];

/**
 * Light / Dark / System. The choice applies at once, is remembered on this
 * device, and is saved to the account so other devices follow it.
 */
export default function ThemeToggle({
  onSaveError,
}: {
  onSaveError?: () => void;
}) {
  const theme = useTheme();

  async function choose(next: Theme) {
    setStoredTheme(next);

    try {
      await api.patch("/settings", { theme: next });
    } catch {
      onSaveError?.();
    }
  }

  return (
    <div
      role="radiogroup"
      aria-label="Theme"
      className="inline-flex max-w-full flex-wrap rounded-full border border-border bg-muted/50 p-1"
    >
      {OPTIONS.map(({ value, label, icon: Icon }) => (
        <button
          key={value}
          type="button"
          role="radio"
          aria-checked={theme === value}
          onClick={() => choose(value)}
          className={cn(
            "flex items-center gap-1.5 whitespace-nowrap rounded-full px-3.5 py-1.5 text-sm font-medium transition",
            theme === value
              ? "bg-card text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <Icon size={14} /> {label}
        </button>
      ))}
    </div>
  );
}
