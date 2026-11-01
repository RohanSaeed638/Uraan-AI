import type { ReactNode } from "react";

import { LEGAL_UPDATED } from "@/lib/site";

export interface LegalSection {
  title: string;
  /** Paragraphs, and bullet lists written as string arrays. */
  body: (string | string[] | ReactNode)[];
}

/** A long-form page: a title, the date it last changed, and numbered sections. */
export default function LegalPage({
  title,
  intro,
  sections,
}: {
  title: string;
  intro: string;
  sections: LegalSection[];
}) {
  return (
    <div className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
      <h1 className="font-heading text-3xl font-bold sm:text-4xl">{title}</h1>
      <p className="mt-2 text-sm text-muted-foreground">Last updated: {LEGAL_UPDATED}</p>
      <p className="mt-6 text-lg text-muted-foreground">{intro}</p>

      <div className="mt-10 space-y-8">
        {sections.map((section, index) => (
          <section key={section.title} aria-labelledby={`s${index}`}>
            <h2 id={`s${index}`} className="font-heading text-xl font-semibold">
              {index + 1}. {section.title}
            </h2>
            <div className="mt-3 space-y-3 text-muted-foreground">
              {section.body.map((block, i) =>
                Array.isArray(block) ? (
                  <ul key={i} className="list-disc space-y-1.5 ps-6">
                    {block.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : typeof block === "string" ? (
                  <p key={i}>{block}</p>
                ) : (
                  <div key={i}>{block}</div>
                )
              )}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
