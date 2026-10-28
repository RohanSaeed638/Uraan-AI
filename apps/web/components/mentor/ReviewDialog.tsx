"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { CheckCircle2, Loader2, Target, TriangleAlert } from "lucide-react";

import { reviewWork } from "@/lib/api/mentor";
import { apiErrorMessage } from "@/lib/profile-options";
import { cn } from "@/lib/utils";
import { ReviewInput, ReviewKind, ReviewResult } from "@/types/api";

import FilterChips from "@/components/shared/FilterChips";
import Pill from "@/components/shared/Pill";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

const KINDS: ReviewKind[] = ["github", "code", "portfolio"];

const PRIORITY_STYLE = {
  high: "bg-destructive/15 text-destructive",
  medium: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
  low: "bg-muted text-muted-foreground",
} as const;

export default function ReviewDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const t = useTranslations("mentorReview");

  const [kind, setKind] = useState<ReviewKind>("github");
  const [url, setUrl] = useState("");
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ReviewResult | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();

    if (kind === "github" && !url.trim()) return setError(t("needUrl"));
    if (kind === "code" && code.trim().length < 20) return setError(t("needCode"));

    const input: ReviewInput = {
      kind,
      note: note.trim() || undefined,
      ...(kind === "github" ? { url: url.trim() } : {}),
      ...(kind === "code"
        ? { code, language: language.trim() || undefined }
        : {}),
    };

    setLoading(true);
    setError(null);

    try {
      setResult(await reviewWork(input));
    } catch (err) {
      setError(apiErrorMessage(err, t("failed")));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{t("title")}</DialogTitle>
          <DialogDescription>{t("description")}</DialogDescription>
        </DialogHeader>

        {result ? (
          <div className="space-y-5 text-sm">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <Pill tone="soft">{t(`verdict.${result.verdict}`)}</Pill>
                <span className="text-xs text-muted-foreground">
                  {t("reviewed", { what: result.reviewed })}
                </span>
              </div>
              <p className="mt-2">{result.summary}</p>
            </div>

            <section>
              <h3 className="flex items-center gap-2 font-semibold">
                <CheckCircle2 size={16} className="text-emerald-500" />
                {t("strengths")}
              </h3>
              <ul className="mt-2 space-y-1.5">
                {result.strengths.map((s) => (
                  <li key={s} className="break-words">
                    {s}
                  </li>
                ))}
              </ul>
            </section>

            <section>
              <h3 className="flex items-center gap-2 font-semibold">
                <TriangleAlert size={16} className="text-amber-500" />
                {t("improvements")}
              </h3>
              <ul className="mt-2 space-y-3">
                {result.improvements.map((item) => (
                  <li key={item.title} className="rounded-2xl border p-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium">{item.title}</span>
                      <span
                        className={cn(
                          "rounded-full px-2 py-0.5 text-xs",
                          PRIORITY_STYLE[item.priority] ?? PRIORITY_STYLE.low
                        )}
                      >
                        {t(`priority.${item.priority}`)}
                      </span>
                    </div>
                    <p className="mt-1 break-words text-muted-foreground">
                      {item.detail}
                    </p>
                  </li>
                ))}
              </ul>
            </section>

            <section>
              <h3 className="flex items-center gap-2 font-semibold">
                <Target size={16} className="text-brand-violet" />
                {t("nextSteps")}
              </h3>
              <ol className="mt-2 list-decimal space-y-1.5 ps-5">
                {result.next_steps.map((s) => (
                  <li key={s} className="break-words">
                    {s}
                  </li>
                ))}
              </ol>
            </section>

            <Button variant="outline" onClick={() => setResult(null)}>
              {t("reviewAnother")}
            </Button>
          </div>
        ) : (
          <form onSubmit={submit} className="space-y-4">
            <FilterChips
              label={t("title")}
              size="sm"
              value={kind}
              onChange={(k) => {
                setKind(k);
                setError(null);
              }}
              options={KINDS.map((k) => ({ value: k, label: t(`kinds.${k}`) }))}
            />

            {kind === "github" && (
              <div className="space-y-2">
                <label htmlFor="review-url" className="text-sm font-medium">
                  {t("urlLabel")}
                </label>
                <Input
                  id="review-url"
                  type="url"
                  inputMode="url"
                  placeholder="https://github.com/you/your-project"
                  value={url}
                  maxLength={300}
                  onChange={(e) => setUrl(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">{t("urlHint")}</p>
              </div>
            )}

            {kind === "code" && (
              <div className="grid gap-4 sm:grid-cols-[1fr_160px]">
                <div className="space-y-2 sm:col-span-2">
                  <label htmlFor="review-code" className="text-sm font-medium">
                    {t("codeLabel")}
                  </label>
                  <Textarea
                    id="review-code"
                    value={code}
                    maxLength={20000}
                    placeholder={t("codePlaceholder")}
                    className="min-h-48 font-mono text-xs"
                    onChange={(e) => setCode(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label htmlFor="review-language" className="text-sm font-medium">
                    {t("languageLabel")}
                  </label>
                  <Input
                    id="review-language"
                    value={language}
                    maxLength={30}
                    placeholder="python"
                    onChange={(e) => setLanguage(e.target.value)}
                  />
                </div>
              </div>
            )}

            {kind === "portfolio" && (
              <p className="rounded-2xl bg-muted/50 p-4 text-sm text-muted-foreground">
                {t("portfolioHint")}
              </p>
            )}

            <div className="space-y-2">
              <label htmlFor="review-note" className="text-sm font-medium">
                {t("noteLabel")}
              </label>
              <Input
                id="review-note"
                value={note}
                maxLength={300}
                placeholder={t("notePlaceholder")}
                onChange={(e) => setNote(e.target.value)}
              />
            </div>

            {error && (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            )}

            <Button type="submit" disabled={loading} className="gap-2">
              {loading && <Loader2 size={15} className="animate-spin" />}
              {loading ? t("reviewing") : t("submit")}
            </Button>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
