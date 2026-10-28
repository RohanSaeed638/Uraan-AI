"use client";

import { useTranslations } from "next-intl";

import { setErrorLookup } from "@/lib/api-errors";

/** Gives plain functions (the API error helpers) access to the `errors`
 * messages of the current language. Renders nothing. */
export default function ErrorTranslator() {
  const t = useTranslations("errors");

  setErrorLookup((code) => (t.has(code) ? t(code) : null));

  return null;
}
