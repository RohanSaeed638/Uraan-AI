// Plain module (no "use client") so both the server page and the client
// component can use it.
export const TAB_KEYS = ["account", "appearance", "preferences", "data"] as const;

export type TabKey = (typeof TAB_KEYS)[number];

export const isTabKey = (value: unknown): value is TabKey =>
  TAB_KEYS.some((key) => key === value);
