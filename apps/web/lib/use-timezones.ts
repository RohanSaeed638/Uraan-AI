"use client";

import { useMemo, useSyncExternalStore } from "react";

import { deviceTimezone, listTimezones } from "@/lib/profile-options";

const noSubscription = () => () => {};
const NONE: string[] = [];

let cachedList: string[] | null = null;
const browserTimezones = () => (cachedList ??= listTimezones());

/**
 * Timezone choices. The full list and the device timezone only exist in the
 * browser, and differ from the server's, so they appear after hydration. The
 * first render only has the values already saved, which match on both sides.
 */
export function useTimezones(...saved: (string | null | undefined)[]) {
  const all = useSyncExternalStore(noSubscription, browserTimezones, () => NONE);
  const device = useSyncExternalStore(noSubscription, deviceTimezone, () => null);

  const key = saved.join("|");

  const options = useMemo(() => {
    const extras = [...saved, device].filter(
      (z, i, arr): z is string => !!z && arr.indexOf(z) === i && !all.includes(z)
    );

    return [...extras, ...all];
    // `saved` is rebuilt on every render; `key` stands in for its contents.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [all, device, key]);

  return { options, device };
}
