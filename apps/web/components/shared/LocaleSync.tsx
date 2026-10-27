"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useLocale } from "next-intl";

import { setLocaleCookie, setWordingCookie } from "@/app/actions/locale";
import { api } from "@/lib/api";
import { WORDING_COOKIE, isLocale, isWording } from "@/i18n/config";
import { getProfile } from "@/lib/api/profile";

/** The language and wording saved on the account win on a new device: signing
 * in on a new phone shows the app as the learner set it. Runs once per visit,
 * and only switches when they differ. */
export default function LocaleSync() {
  const router = useRouter();
  const current = useLocale();

  useEffect(() => {
    if (sessionStorage.getItem("uraan-locale-synced")) return;

    sessionStorage.setItem("uraan-locale-synced", "1");

    const wording = document.cookie
      .split("; ")
      .find((c) => c.startsWith(`${WORDING_COOKIE}=`))
      ?.split("=")[1];

    Promise.all([
      getProfile() as Promise<{ language?: string }>,
      api.get<{ wording?: string }>("/settings").then((r) => r.data),
    ])
      .then(async ([profile, settings]) => {
        let changed = false;

        if (isLocale(profile?.language) && profile.language !== current) {
          await setLocaleCookie(profile.language);
          changed = true;
        }

        if (isWording(settings?.wording) && settings.wording !== (wording ?? "classic")) {
          await setWordingCookie(settings.wording);
          changed = true;
        }

        if (changed) router.refresh();
      })
      .catch(() => {
        // Offline or signed out: keep what this device has.
      });
  }, [current, router]);

  return null;
}
