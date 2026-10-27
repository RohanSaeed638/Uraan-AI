"use server";

import { cookies } from "next/headers";

import { LOCALE_COOKIE, WORDING_COOKIE, isLocale, isWording } from "@/i18n/config";

/** Remembers the language for a year; the page reads it on the next render. */
export async function setLocaleCookie(locale: string) {
  if (!isLocale(locale)) return;

  (await cookies()).set(LOCALE_COOKIE, locale, {
    path: "/",
    maxAge: 60 * 60 * 24 * 365,
    sameSite: "lax",
  });
}

/** Remembers classic or gamified wording for a year. */
export async function setWordingCookie(wording: string) {
  if (!isWording(wording)) return;

  (await cookies()).set(WORDING_COOKIE, wording, {
    path: "/",
    maxAge: 60 * 60 * 24 * 365,
    sameSite: "lax",
  });
}
