"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { toast } from "sonner";

import { answerQuestion, finishInterview } from "@/lib/api/interviews";
import { InterviewSession, InterviewTurn } from "@/types/api";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import LoadingButton from "@/components/shared/LoadingButton";

function errorMessage(error: unknown, fallback: string) {
  const detail = (error as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}

function Scores({ turn }: { turn: InterviewTurn }) {
  const items = [
    ["Technical", turn.technical_score],
    ["Communication", turn.communication_score],
    ["Confidence", turn.confidence_score],
  ] as const;

  return (
    <div className="flex flex-wrap gap-2">
      {items.map(([label, value]) => (
        <span
          key={label}
          className="rounded-full bg-brand-violet/10 px-3 py-1 text-xs font-medium text-brand-violet"
        >
          {label} {value}/10
        </span>
      ))}
    </div>
  );
}

function Results({ session }: { session: InterviewSession }) {
  return (
    <div className="space-y-6">
      <Card className="gap-4 p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Overall score</p>
            <p className="font-heading whitespace-nowrap text-4xl font-bold">
              {Math.round(session.overall_score ?? 0)}%
            </p>
          </div>
          {session.averages && (
            <div className="grid w-full grid-cols-3 gap-2 text-center text-sm sm:w-auto sm:gap-4">
              {(
                [
                  ["Technical", session.averages.technical],
                  ["Communication", session.averages.communication],
                  ["Confidence", session.averages.confidence],
                ] as const
              ).map(([label, value]) => (
                <div key={label}>
                  <p className="text-lg font-bold">{value}</p>
                  <p className="whitespace-nowrap text-xs text-muted-foreground">{label}</p>
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
              ["Strengths", session.summary.strengths],
              ["To improve", session.summary.improvements],
              ["Next steps", session.summary.next_steps],
            ] as const
          ).map(([title, items]) => (
            <Card key={title} className="gap-2 p-5">
              <p className="text-sm font-semibold">{title}</p>
              <ul className="list-disc space-y-1 pl-4 text-sm text-muted-foreground">
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
              <p className="text-sm text-muted-foreground">Skipped.</p>
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
  const [session, setSession] = useState(initial);
  const [draft, setDraft] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [justAnswered, setJustAnswered] = useState<InterviewTurn | null>(null);

  const completed = session.status === "completed";
  const next = session.turns.find((t) => t.answer === null) ?? null;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!next || !draft.trim()) return;
    setSubmitting(true);
    try {
      const turn = await answerQuestion(session.id, next.order, draft.trim());
      setSession((prev) => ({
        ...prev,
        answered: prev.answered + 1,
        turns: prev.turns.map((t) => (t.order === turn.order ? turn : t)),
      }));
      setJustAnswered(turn);
      setDraft("");
    } catch (err) {
      toast.error(errorMessage(err, "Couldn't review your answer."));
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
      toast.error(errorMessage(err, "Couldn't finish the interview."));
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
        <ArrowLeft size={15} /> All interviews
      </Link>

      <h1 className="font-heading mt-3 text-2xl font-bold">{session.role}</h1>
      <p className="text-sm capitalize text-muted-foreground">
        {session.difficulty} · {session.answered}/{session.total} answered
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
                  Next question
                </Button>
              )}
              <LoadingButton
                variant={next ? "outline" : "default"}
                loading={finishing}
                onClick={finish}
              >
                {next ? "Finish now" : "See my results"}
              </LoadingButton>
            </div>
          </Card>
        ) : next ? (
          <Card className="gap-4 p-6">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">
              Question {next.order} of {session.total}
            </p>
            <p className="text-lg font-medium">{next.question}</p>
            <form onSubmit={submit} className="space-y-3">
              <Textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Type your answer as you would say it in the interview…"
                maxLength={4000}
                className="min-h-36"
                aria-label="Your answer"
              />
              <div className="flex flex-wrap gap-2">
                <LoadingButton
                  type="submit"
                  loading={submitting}
                  disabled={!draft.trim()}
                >
                  Submit answer
                </LoadingButton>
                {session.answered > 0 && (
                  <LoadingButton
                    type="button"
                    variant="outline"
                    loading={finishing}
                    onClick={finish}
                  >
                    Finish now
                  </LoadingButton>
                )}
              </div>
            </form>
          </Card>
        ) : (
          <Card className="gap-3 p-6">
            <p className="font-medium">All questions answered.</p>
            <LoadingButton loading={finishing} onClick={finish} className="self-start">
              See my results
            </LoadingButton>
          </Card>
        )}
      </div>
    </div>
  );
}
