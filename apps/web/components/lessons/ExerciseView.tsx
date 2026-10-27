"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Check, Copy, Eye, Lightbulb } from "lucide-react";

import { ExerciseDetails } from "@/types/roadmap";

import SimpleMarkdown from "@/components/shared/SimpleMarkdown";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

function CodeBlock({ code, label }: { code: string; label: string }) {
  const t = useTranslations("exercise");
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      toast.error(t("copyFailed"));
    }
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-muted/40">
      <div className="flex items-center justify-between gap-2 border-b border-border px-4 py-2 text-xs text-muted-foreground">
        <span>{label}</span>
        <button
          type="button"
          onClick={copy}
          className="inline-flex items-center gap-1.5 rounded-full px-2 py-1 hover:bg-muted hover:text-foreground"
        >
          {copied ? <Check size={13} /> : <Copy size={13} />}
          {copied ? t("copied") : t("copy")}
        </button>
      </div>
      <pre className="overflow-x-auto p-4 text-sm leading-6">
        <code>{code}</code>
      </pre>
    </div>
  );
}

/** A coding exercise: problem, starter code, hints one at a time, and a
 * solution that is only shown when asked for (after a confirmation). */
export default function ExerciseView({
  problem,
  details,
}: {
  problem: string | null;
  details: ExerciseDetails;
}) {
  const t = useTranslations("exercise");

  const [hintsShown, setHintsShown] = useState(0);
  const [confirming, setConfirming] = useState(false);
  const [solutionShown, setSolutionShown] = useState(false);

  const hints = details.hints ?? [];

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm">
        <p className="font-semibold text-emerald-700 dark:text-emerald-400">
          {t("banner")}
        </p>
        <p className="mt-1 text-muted-foreground">{t("bannerText")}</p>
      </div>

      {problem && (
        <Card className="p-6 sm:p-8">
          <h2 className="font-heading text-lg font-semibold">{t("problem")}</h2>
          <div className="mt-3">
            <SimpleMarkdown source={problem} />
          </div>
          {details.expected_output && (
            <p className="mt-4 text-sm text-muted-foreground">
              {t("expected")}{" "}
              <code className="rounded bg-muted px-1.5 py-0.5">
                {details.expected_output}
              </code>
            </p>
          )}
        </Card>
      )}

      <CodeBlock
        code={details.starter_code}
        label={t("starter", { language: details.language })}
      />

      <section aria-labelledby="hints-title">
        <h2 id="hints-title" className="font-heading flex items-center gap-2 text-lg font-semibold">
          <Lightbulb size={18} className="text-amber-500" /> {t("hints")}
        </h2>

        {hintsShown > 0 && (
          <ol className="mt-3 space-y-2">
            {hints.slice(0, hintsShown).map((hint, i) => (
              <li key={i} className="rounded-2xl border border-border p-4 text-sm">
                <span className="me-2 font-semibold text-amber-600 dark:text-amber-400">
                  {t("hintNumber", { number: i + 1 })}
                </span>
                {hint}
              </li>
            ))}
          </ol>
        )}

        {hintsShown < hints.length ? (
          <Button
            variant="outline"
            size="sm"
            className="mt-3"
            onClick={() => setHintsShown((n) => n + 1)}
          >
            {hintsShown === 0 ? t("showHint") : t("showNextHint")}
          </Button>
        ) : (
          hints.length > 0 && (
            <p className="mt-3 text-sm text-muted-foreground">{t("noMoreHints")}</p>
          )
        )}
      </section>

      <section aria-labelledby="solution-title">
        <h2 id="solution-title" className="font-heading flex items-center gap-2 text-lg font-semibold">
          <Eye size={18} className="text-muted-foreground" /> {t("solution")}
        </h2>

        {solutionShown ? (
          <div className="mt-3">
            <CodeBlock code={details.solution} label={t("solutionLabel")} />
          </div>
        ) : confirming ? (
          <div className="mt-3 rounded-2xl border border-border p-4 text-sm">
            <p>{t("confirmText")}</p>
            <div className="mt-3 flex gap-2">
              <Button size="sm" onClick={() => setSolutionShown(true)}>
                {t("confirmShow")}
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setConfirming(false)}>
                {t("keepTrying")}
              </Button>
            </div>
          </div>
        ) : (
          <Button
            variant="outline"
            size="sm"
            className="mt-3"
            onClick={() => setConfirming(true)}
          >
            {t("showSolution")}
          </Button>
        )}
      </section>
    </div>
  );
}
