"use client";

import { Toaster } from "sonner";

import { useIsDark } from "@/lib/theme";

/** Toasts that match the app theme instead of always being dark. */
export default function AppToaster() {
  const dark = useIsDark();

  return <Toaster richColors theme={dark ? "dark" : "light"} />;
}
