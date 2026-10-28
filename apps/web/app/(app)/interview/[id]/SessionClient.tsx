"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { ArrowLeft } from "lucide-react";
import { toast } from "sonner";

import { answerQuestion, finishInterview } from "@/lib/api/interviews";
import { InterviewSession, InterviewTurn } from "@/types/api";
import { apiErrorMessage } from "@/lib/profile-options";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import LoadingButton from "@/components/shared/LoadingButton";

function Scores({ turn }: { turn: InterviewTurn }) {
  const t = useTranslations("interview");
  const items = [
    ["technical", turn.technical_score],
    ["communication", turn.communication_score],
    ["confidence", turn.confidence_score],
  ] as const;

  return (
    <div className="flex flex-wrap gap-2">
      {items.map(([label, value]) => (
        <span
          key={label}
          className="rounded-full bg-brand-violet/10 px-3 py-1 text-xs font-medium text-brand-gold-deep dark:text-brand-gold"
        >
          {t("score", { label: t(label), value: value ?? "–" })}
        </span>
      ))}
    </div>
  );
}

function Results({ session }: { session: InterviewSession }) {
  const t = useTranslations("interview");

  return (
    <div className="space-y-6">
      <Card className="gap-4 p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{t("overall")}</p>
            <p className="font-heading whitespace-nowrap text-4xl font-bold">
              {Math.round(session.overall_score ?? 0)}%
            </p>
          </div>
          {session.averages && (
            <div className="grid w-full grid-cols-3 gap-2 text-center text-sm sm:w-auto sm:gap-4">
              {(
                [
                  ["technical", session.averages.technical],
                  ["communication", session.averages.communication],
                  ["confidence", session.averages.confidence],
                ] as const
              ).map(([label, value]) => (
                <div key={label}>
                  <p className="text-lg font-bold">{value}</p>
                  <p className="whitespace-nowrap text-xs text-muted-foreground">{t(label)}</p>
                </div>
              ))}
            </div>
          )}
        </div>
        <Progress value={Math.round(session.overall_score ?? 0)} />
      </Card>

      {session.summary && (
        <div className="grid gap-4 md:grid-cols-3">
          {(
            [
              ["strengths", session.summary.strengths],
              ["improve", session.summary.improvements],
              ["nextSteps", session.summary.next_steps],
            ] as const
          ).map(([title, items]) => (
            <Card key={title} className="gap-2 p-5">
              <p className="text-sm font-semibold">{t(title)}</p>
              <ul className="list-disc space-y-1 ps-4 text-sm text-muted-foreground">
                {items.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
      )}

      <div className="space-y-4">
        {session.turns.map((turn) => (
          <Card key={turn.order} className="gap-3 p-5">
            <p className="font-medium">
              {turn.order}. {turn.question}
            </p>
            {turn.answer === null ? (
              <p className="text-sm text-muted-foreground">{t("skipped")}</p>
            ) : (
              <>
                <p className="whitespace-pre-wrap rounded-xl bg-muted/50 p-3 text-sm">
                  {turn.answer}
                </p>
                <Scores turn={turn} />
                <p className="text-sm text-muted-foreground">{turn.feedback}</p>
              </>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}

export default function SessionClient({ initial }: { initial: InterviewSession }) {
  const t = useTranslations("interview");
  const tLevel = useTranslations("options.skill_level");
  const [session, setSession] = useState(initial);
  const [draft, setDraft] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [justAnswered, setJustAnswered] = useState<InterviewTurn | null>(null);

  const completed = session.status === "completed";
  const next = session.turns.find((turn) => turn.answer === null) ?? null;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!next || !draft.trim()) return;
    setSubmitting(true);
    try {
      const turn = await answerQuestion(session.id, next.order, draft.trim());
      setSession((prev) => ({
        ...prev,
        answered: prev.answered + 1,
        turns: prev.turns.map((x) => (x.order === turn.order ? turn : x)),
      }));
      setJustAnswered(turn);
      setDraft("");
    } catch (err) {
      toast.error(apiErrorMessage(err, t("reviewFailed")));
    } finally {
      setSubmitting(false);
    }
  }

  async function finish() {
    setFinishing(true);
    try {
      setSession(await finishInterview(session.id));
      setJustAnswered(null);
    } catch (err) {
      toast.error(apiErrorMessage(err, t("finishFailed")));
    } finally {
      setFinishing(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <Link
        href="/interview"
        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft size={15} className="rtl:rotate-180" /> {t("all")}
      </Link>

      <h1 className="font-heading mt-3 text-2xl font-bold">{session.role}</h1>
      <p className="text-sm text-muted-foreground">
        {t("answeredShort", {
          level: tLevel(session.difficulty),
          answered: session.answered,
          total: session.total,
        })}
      </p>

      <div className="mt-6">
        {completed ? (
          <Results session={session} />
        ) : justAnswered ? (
          <Card className="gap-4 p-6">
            <p className="font-medium">
              {justAnswered.order}. {justAnswered.question}
            </p>
            <Scores turn={justAnswered} />
            <p className="text-sm text-muted-foreground">
              {justAnswered.feedback}
            </p>
            <div className="flex flex-wrap gap-2">
              {next && (
                <Button onClick={() => setJustAnswered(null)}>
                  {t("nextQuestion")}
                </Button>
              )}
              <LoadingButton
                variant={next ? "outline" : "default"}
                loading={finishing}
                onClick={finish}
              >
                {next ? t("finishNow") : t("seeResults")}
              </LoadingButton>
            </div>
          </Card>
        ) : next ? (
          <Card className="gap-4 p-6">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">
              {t("questionOf", { current: next.order, total: session.total })}
            </p>
            <p className="text-lg font-medium">{next.question}</p>
            <form onSubmit={submit} className="space-y-3">
              <Textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder={t("answerHint")}
                maxLength={4000}
                className="min-h-36"
                aria-label={t("yourAnswer")}
              />
              <div className="flex flex-wrap gap-2">
                <LoadingButton
                  type="submit"
                  loading={submitting}
                  disabled={!draft.trim()}
                >
                  {t("submit")}
                </LoadingButton>
                {session.answered > 0 && (
                  <LoadingButton
                    type="button"
                    variant="outline"
                    loading={finishing}
                    onClick={finish}
                  >
                    {t("finishNow")}
                  </LoadingButton>
                )}
              </div>
            </form>
          </Card>
        ) : (
          <Card className="gap-3 p-6">
            <p className="font-medium">{t("allAnswered")}</p>
            <LoadingButton loading={finishing} onClick={finish} className="self-start">
              {t("seeResults")}
            </LoadingButton>
          </Card>
        )}
      </div>
    </div>
  );
}
