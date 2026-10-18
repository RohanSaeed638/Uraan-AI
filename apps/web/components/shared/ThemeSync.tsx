"use client";

import { useEffect } from "react";

import { api } from "@/lib/api";
import { applyTheme, getStoredTheme, setStoredTheme, Theme } from "@/lib/theme";

/**
 * Keeps the theme right across devices: when this device has no saved
 * choice yet, the one saved on the account is applied; and "System" follows
 * the operating system as it changes.
 */
export default function ThemeSync() {
  useEffect(() => {
    let cancelled = false;

    const stored = getStoredTheme();

    if (stored) {
      applyTheme(stored);
    } else {
      api
        .get<{ theme: Theme }>("/settings")
        .then(({ data }) => {
          // Nothing was chosen here in the meantime.
          if (!cancelled && !getStoredTheme() && data.theme) {
            setStoredTheme(data.theme);
          }
        })
        .catch(() => {
          // Offline or signed out: keep the default.
        });
    }

    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      const current = getStoredTheme();
      if (current === "system") applyTheme(current);
    };

    media.addEventListener("change", onChange);

    return () => {
      cancelled = true;
      media.removeEventListener("change", onChange);
    };
  }, []);

  return null;
}
