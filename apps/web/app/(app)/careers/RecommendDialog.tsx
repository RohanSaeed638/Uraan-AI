"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";

import { careerText } from "@/lib/career-text";
import { Loader2, Sparkles } from "lucide-react";

import { recommendCareers } from "@/lib/api/careers";
import { apiErrorMessage } from "@/lib/profile-options";
import { CareerRecommendation } from "@/types/api";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function RecommendDialog({ open, onOpenChange }: Props) {
  const t = useTranslations("careers.recommend");
  const ct = careerText(useTranslations("catalog"));

  const [interests, setInterests] = useState("");
  const [experience, setExperience] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<CareerRecommendation[] | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();

    if (interests.trim().length < 3) {
      setError(t("interestsRequired"));
      return;
    }

    setLoading(true);
    setError(null);

    try {
      setResults(
        await recommendCareers({
          interests: interests.trim(),
          experience: experience.trim() || undefined,
        })
      );
    } catch (err) {
      setError(apiErrorMessage(err, t("failed")));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{t("title")}</DialogTitle>
          <DialogDescription>{t("description")}</DialogDescription>
        </DialogHeader>

        {results ? (
          <div className="space-y-4">
            {results.map(({ career, reason }, i) => (
              <div key={career.slug} className="rounded-2xl border p-4">
                <p className="text-xs text-muted-foreground">
                  {t("match", { rank: i + 1 })}
                </p>
                <p className="font-heading text-lg font-semibold">{ct.name(career.slug, career.name)}</p>
                <p className="mt-1 text-sm text-muted-foreground">{reason}</p>

                <div className="mt-3 flex flex-wrap gap-2">
                  <Link
                    href={`/careers/${career.slug}`}
                    className={buttonVariants({ variant: "outline", size: "sm" })}
                    onClick={() => onOpenChange(false)}
                  >
                    {t("viewCareer")}
                  </Link>
                  <Link
                    href={`/roadmaps?career=${career.slug}`}
                    className={buttonVariants({ size: "sm" })}
                  >
                    {t("makeRoadmap")}
                  </Link>
                </div>
              </div>
            ))}

            <Button variant="ghost" onClick={() => setResults(null)}>
              {t("tryAgain")}
            </Button>
          </div>
        ) : (
          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="rec-interests" className="text-sm font-medium">
                {t("interests")}
              </label>
              <Textarea
                id="rec-interests"
                value={interests}
                maxLength={500}
                placeholder={t("interestsPlaceholder")}
                className="min-h-24"
                onChange={(e) => setInterests(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="rec-experience" className="text-sm font-medium">
                {t("experience")}
              </label>
              <Input
                id="rec-experience"
                value={experience}
                maxLength={300}
                placeholder={t("experiencePlaceholder")}
                onChange={(e) => setExperience(e.target.value)}
              />
            </div>

            <p className="text-xs text-muted-foreground">{t("profileNote")}</p>

            {error && (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            )}

            <Button type="submit" disabled={loading} className="gap-2">
              {loading ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Sparkles size={16} />
              )}
              {loading ? t("thinking") : t("submit")}
            </Button>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
