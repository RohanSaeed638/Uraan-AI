"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { CheckCircle2, Loader2, RotateCcw, XCircle } from "lucide-react";
import { toast } from "sonner";

import { getQuiz, submitQuiz } from "@/lib/api/quiz";
import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function TaskQuiz({ taskId }: { taskId: string }) {
  const [started, setStarted] = useState(false);
  const [selected, setSelected] = useState<Record<string, number>>({});

  // Fetched on demand: the first request asks the backend to generate it.
  const quiz = useQuery({
    queryKey: ["quiz", taskId],
    queryFn: () => getQuiz(taskId),
    enabled: started,
    staleTime: Infinity,
    retry: false,
  });

  const submit = useMutation({
    mutationFn: () =>
      submitQuiz(
        taskId,
        Object.entries(selected).map(([question_id, selected_option]) => ({
          question_id,
          selected_option,
        }))
      ),
    onError: () => toast.error("Couldn't submit your answers. Try again."),
  });

  const questions = quiz.data ?? [];
  const result = submit.data;
  const answeredAll =
    questions.length > 0 && questions.every((q) => q.id in selected);

  function retake() {
    setSelected({});
    submit.reset();
  }

  if (!started) {
    return (
      <Card className="flex-row items-center justify-between gap-4 p-6">
        <div>
          <h2 className="font-semibold">Check your understanding</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Take a short quiz on this task. You need 70% to pass.
          </p>
        </div>
        <Button onClick={() => setStarted(true)}>Start quiz</Button>
      </Card>
    );
  }

  if (quiz.isLoading) {
    return (
      <Card className="flex-row items-center gap-3 p-6 text-sm text-muted-foreground">
        <Loader2 size={16} className="animate-spin" />
        Preparing your quiz…
      </Card>
    );
  }

  if (quiz.isError) {
    return (
      <Card className="flex-row items-center justify-between gap-4 p-6">
        <p className="text-sm text-muted-foreground">
          We couldn&apos;t load the quiz.
        </p>
        <Button variant="outline" onClick={() => quiz.refetch()}>
          Try again
        </Button>
      </Card>
    );
  }

  return (
    <Card className="gap-6 p-6">
      <div className="flex items-start justify-between gap-4">
        <h2 className="font-semibold">Quiz</h2>
        {result && (
          <p
            className={cn(
              "text-sm font-semibold",
              result.passed ? "text-emerald-600" : "text-destructive"
            )}
          >
            {result.correct_answers}/{result.total_questions} ·{" "}
            {Math.round(result.score_percentage)}% ·{" "}
            {result.passed ? "Passed" : "Not passed"}
          </p>
        )}
      </div>

      {questions.map((q, index) => {
        const graded = result?.results.find((r) => r.question_id === q.id);

        return (
          <div key={q.id} className="space-y-3">
            <p className="text-sm font-medium">
              {index + 1}. {q.question}
            </p>

            <div className="space-y-2">
              {q.options.map((option, i) => {
                const isSelected = selected[q.id] === i;
                const isCorrect = graded?.correct_option === i;
                const isWrongPick = graded && isSelected && !graded.is_correct;

                return (
                  <button
                    key={i}
                    type="button"
                    disabled={!!result}
                    onClick={() =>
                      setSelected((prev) => ({ ...prev, [q.id]: i }))
                    }
                    className={cn(
                      "flex w-full items-center justify-between gap-3 rounded-xl border px-4 py-2.5 text-left text-sm transition",
                      !result && isSelected
                        ? "border-brand-violet bg-brand-violet/10"
                        : "hover:bg-muted",
                      isCorrect && "border-emerald-500 bg-emerald-500/10",
                      isWrongPick && "border-destructive bg-destructive/10"
                    )}
                  >
                    <span>{option}</span>
                    {isCorrect && (
                      <CheckCircle2 size={16} className="text-emerald-600" />
                    )}
                    {isWrongPick && (
                      <XCircle size={16} className="text-destructive" />
                    )}
                  </button>
                );
              })}
            </div>

            {graded?.explanation && (
              <p className="text-xs text-muted-foreground">
                {graded.explanation}
              </p>
            )}
          </div>
        );
      })}

      {result ? (
        <Button variant="outline" className="gap-2 self-start" onClick={retake}>
          <RotateCcw size={14} /> Retake quiz
        </Button>
      ) : (
        <Button
          className="self-start"
          disabled={!answeredAll || submit.isPending}
          onClick={() => submit.mutate()}
        >
          {submit.isPending ? "Submitting…" : "Submit answers"}
        </Button>
      )}
    </Card>
  );
}
