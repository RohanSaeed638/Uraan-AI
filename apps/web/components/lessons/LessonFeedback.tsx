"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, ThumbsDown, ThumbsUp } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { toast } from "sonner";

import {
  FEEDBACK_REASONS,
  getLessonFeedback,
  saveLessonFeedback,
  type FeedbackReason,
  type LessonFeedback as Vote,
} from "@/lib/api/feedback";
import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

/**
 * "Was this lesson helpful?" at the end of a lesson. Lessons are written by AI, so this is how a wrong or
 * poor one gets noticed. A "no" is saved the moment it is tapped (so it is never lost), and the learner may
 * then say what was wrong. Mount it with a `key` of the lesson, so each lesson starts fresh.
 */
export default function LessonFeedback({ unitId }: { unitId: string }) {
  const t = useTranslations("feedback");
  const queryClient = useQueryClient();
  const key = ["lesson-feedback", unitId];

  const saved = useQuery({ queryKey: key, queryFn: () => getLessonFeedback(unitId), retry: false });

  const [reason, setReason] = useState<FeedbackReason | null>(null);
  const [comment, setComment] = useState("");
  const [detailsSent, setDetailsSent] = useState(false);
  const [busy, setBusy] = useState(false);

  const vote: Vote | null | undefined = saved.data;

  async function save(helpful: boolean, extra?: { reason?: FeedbackReason | null; comment?: string | null }) {
    setBusy(true);

    try {
      const result = await saveLessonFeedback(unitId, { helpful, ...extra });
      queryClient.setQueryData(key, result);

      return true;
    } catch {
      toast.error(t("failed"));

      return false;
    } finally {
      setBusy(false);
    }
  }

  async function sendDetails() {
    if (await save(false, { reason, comment: comment.trim() || null })) setDetailsSent(true);
  }

  // Nothing is shown until we know whether they already voted (it would flicker).
  if (saved.isLoading) return null;

  return (
    <section aria-label={t("title")} className="mt-10 rounded-2xl border border-border bg-card/60 p-5">
      {!vote ? (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm font-medium">{t("title")}</p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="gap-2" disabled={busy} onClick={() => save(true)}>
              <ThumbsUp size={15} aria-hidden /> {t("yes")}
            </Button>
            <Button variant="outline" size="sm" className="gap-2" disabled={busy} onClick={() => save(false)}>
              <ThumbsDown size={15} aria-hidden /> {t("no")}
            </Button>
          </div>
        </div>
      ) : vote.helpful ? (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="flex items-center gap-2 text-sm font-medium">
            <Check size={16} className="text-emerald-500" aria-hidden /> {t("thanks")}
          </p>
          <Button variant="ghost" size="sm" disabled={busy} onClick={() => save(false)}>
            {t("change")}
          </Button>
        </div>
      ) : detailsSent || vote.reason || vote.comment ? (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="flex items-center gap-2 text-sm font-medium">
            <Check size={16} className="text-emerald-500" aria-hidden /> {t("detailsThanks")}
          </p>
          <Button variant="ghost" size="sm" disabled={busy} onClick={() => save(true)}>
            {t("change")}
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-sm font-medium">{t("whatWasWrong")}</p>

          <div className="flex flex-wrap gap-2" role="radiogroup" aria-label={t("whatWasWrong")}>
            {FEEDBACK_REASONS.map((value) => (
              <button
                key={value}
                type="button"
                role="radio"
                aria-checked={reason === value}
                onClick={() => setReason(value)}
                className={cn(
                  "rounded-full border px-3.5 py-1.5 text-sm transition outline-none focus-visible:ring-3 focus-visible:ring-ring/40",
                  reason === value
                    ? "border-brand-violet bg-brand-violet/15 font-medium"
                    : "border-border bg-card text-muted-foreground hover:border-brand-violet/60 hover:text-foreground"
                )}
              >
                {t(`reasons.${value}`)}
              </button>
            ))}
          </div>

          <Textarea
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            maxLength={500}
            rows={3}
            placeholder={t("commentPlaceholder")}
            aria-label={t("commentPlaceholder")}
          />

          <div className="flex items-center gap-3">
            <Button size="sm" disabled={busy || (!reason && !comment.trim())} onClick={sendDetails}>
              {t("send")}
            </Button>
            <Button variant="ghost" size="sm" disabled={busy} onClick={() => setDetailsSent(true)}>
              {t("skip")}
            </Button>
          </div>
        </div>
      )}
    </section>
  );
}
