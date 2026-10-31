"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";

// Last-resort page when the root layout itself crashes. It sits outside the
// providers, so it cannot use translations; the text is kept short and plain.
export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, sans-serif", padding: "4rem 1rem", textAlign: "center" }}>
        <h1>Something went wrong</h1>
        <p>We have been told about it. Please try again.</p>
        <button onClick={reset} style={{ padding: "0.5rem 1rem", cursor: "pointer" }}>
          Try again
        </button>
      </body>
    </html>
  );
}
