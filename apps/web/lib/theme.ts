"use client";

import { useSyncExternalStore } from "react";

export type Theme = "light" | "dark" | "system";

const KEY = "uraan-theme";
const EVENT = "uraan-theme-change";

/** What the app looks like before anyone chooses. */
export const DEFAULT_THEME: Theme = "dark";

function isTheme(value: unknown): value is Theme {
  return value === "light" || value === "dark" || value === "system";
}

/** The saved choice on this device, or null if none was made yet. */
export function getStoredTheme(): Theme | null {
  try {
    const value = localStorage.getItem(KEY);
    return isTheme(value) ? value : null;
  } catch {
    return null;
  }
}

export function resolveDark(theme: Theme): boolean {
  if (theme === "system") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  return theme === "dark";
}

export function applyTheme(theme: Theme) {
  document.documentElement.classList.toggle("dark", resolveDark(theme));
}

/** Saves the choice on this device and applies it straight away. */
export function setStoredTheme(theme: Theme) {
  try {
    localStorage.setItem(KEY, theme);
  } catch {
    // Private mode: the theme still applies for this visit.
  }

  applyTheme(theme);
  window.dispatchEvent(new Event(EVENT));
}

function subscribe(onChange: () => void) {
  const media = window.matchMedia("(prefers-color-scheme: dark)");

  window.addEventListener("storage", onChange);
  window.addEventListener(EVENT, onChange);
  media.addEventListener("change", onChange);

  return () => {
    window.removeEventListener("storage", onChange);
    window.removeEventListener(EVENT, onChange);
    media.removeEventListener("change", onChange);
  };
}

/** The chosen theme ("light", "dark" or "system"). */
export function useTheme(): Theme {
  return useSyncExternalStore(
    subscribe,
    () => getStoredTheme() ?? DEFAULT_THEME,
    () => DEFAULT_THEME
  );
}

/** Whether the app is showing its dark palette right now. */
export function useIsDark(): boolean {
  const theme = useTheme();

  return useSyncExternalStore(
    subscribe,
    () => resolveDark(theme),
    () => true
  );
}
