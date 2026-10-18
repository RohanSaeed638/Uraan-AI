"use client";

import { useEffect, useSyncExternalStore } from "react";
import { Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";

const THEME_KEY = "uraan-theme";
const THEME_EVENT = "uraan-theme-change";

function subscribe(onChange: () => void) {
  window.addEventListener("storage", onChange);
  window.addEventListener(THEME_EVENT, onChange);
  return () => {
    window.removeEventListener("storage", onChange);
    window.removeEventListener(THEME_EVENT, onChange);
  };
}

function getIsDark() {
  const stored = localStorage.getItem(THEME_KEY);
  return stored ? stored === "dark" : true;
}

export default function ThemeToggle() {
  const isDark = useSyncExternalStore(subscribe, getIsDark, () => true);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
  }, [isDark]);

  function setTheme(dark: boolean) {
    localStorage.setItem(THEME_KEY, dark ? "dark" : "light");
    window.dispatchEvent(new Event(THEME_EVENT));
  }

  return (
    <div className="inline-flex rounded-full border border-border bg-muted/50 p-1">
      <button
        type="button"
        onClick={() => setTheme(false)}
        className={cn(
          "flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-sm font-medium transition",
          !isDark
            ? "bg-card text-foreground shadow-sm"
            : "text-muted-foreground"
        )}
      >
        <Sun size={14} /> Light
      </button>
      <button
        type="button"
        onClick={() => setTheme(true)}
        className={cn(
          "flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-sm font-medium transition",
          isDark
            ? "bg-card text-foreground shadow-sm"
            : "text-muted-foreground"
        )}
      >
        <Moon size={14} /> Dark
      </button>
    </div>
  );
}
