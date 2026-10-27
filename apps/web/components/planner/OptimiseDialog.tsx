"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Sparkles } from "lucide-react";

import { apiErrorMessage } from "@/lib/profile-options";

import LoadingButton from "@/components/shared/LoadingButton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";

const EXAMPLES = ["exams", "weekends", "evenings", "travel"] as const;

export default function OptimiseDialog({
  open,
  onOpenChange,
  initial,
  onSubmit,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** What the learner wrote last time, to edit rather than retype. */
  initial: string;
  onSubmit: (request: string) => Promise<void>;
}) {
  const t = useTranslations("planner.optimise");

  const [text, setText] = useState(initial);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();

    if (text.trim().length < 5) {
      setError(t("tooShort"));
      return;
    }

    setSaving(true);
    setError(null);

    try {
      await onSubmit(text.trim());
      onOpenChange(false);
    } catch (err) {
      setError(apiErrorMessage(err, t("failed")));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("title")}</DialogTitle>
          <DialogDescription>{t("description")}</DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="optimise-text" className="text-sm font-medium">
              {t("label")}
            </label>
            <Textarea
              id="optimise-text"
              value={text}
              maxLength={500}
              className="min-h-28"
              placeholder={t("placeholder")}
              onChange={(e) => setText(e.target.value)}
            />
          </div>

          <div>
            <p className="text-xs font-medium text-muted-foreground">{t("tryThese")}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {EXAMPLES.map((key) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setText(t(`examples.${key}`))}
                  className="rounded-full border border-border px-3 py-1 text-xs transition hover:border-brand-gold/60 hover:bg-brand-gold/10"
                >
                  {t(`examples.${key}`)}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}

          <LoadingButton type="submit" loading={saving} className="gap-2">
            <Sparkles size={15} /> {t("submit")}
          </LoadingButton>
        </form>
      </DialogContent>
    </Dialog>
  );
}
