"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";

export default function ThemeToggle() {
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("uraan-theme");
    const dark = stored ? stored === "dark" : true;
    setIsDark(dark);
    document.documentElement.classList.toggle("dark", dark);
  }, []);

  function setTheme(dark: boolean) {
    setIsDark(dark);
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("uraan-theme", dark ? "dark" : "light");
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
