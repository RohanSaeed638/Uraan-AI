import * as Sentry from "@sentry/nextjs";

// Server-side error reporting. Does nothing unless SENTRY_DSN is set.
export async function register() {
  const dsn = process.env.SENTRY_DSN || process.env.NEXT_PUBLIC_SENTRY_DSN;

  if (!dsn) return;

  Sentry.init({
    dsn,
    environment: process.env.APP_ENV || process.env.NODE_ENV,
    tracesSampleRate: 0.1,
  });
}

export const onRequestError = Sentry.captureRequestError;
