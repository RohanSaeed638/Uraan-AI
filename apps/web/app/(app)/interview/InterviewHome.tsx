"use client";

import { useState } from "react";
import PageHeader from "@/components/shared/PageHeader";
import FilterChips from "@/components/shared/FilterChips";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { Mic, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { deleteInterview, startInterview } from "@/lib/api/interviews";
import { Difficulty, InterviewListItem } from "@/types/api";

import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import LoadingButton from "@/components/shared/LoadingButton";
import { cn } from "@/lib/utils";
import { formatDate } from "@/lib/format";
import { apiErrorMessage } from "@/lib/profile-options";

const LEVELS: (Difficulty | "")[] = ["", "beginner", "intermediate", "advanced"];

export default function InterviewHome({
  initialSessions,
}: {
  initialSessions: InterviewListItem[];
}) {
  const router = useRouter();
  const t = useTranslations("interview");
  const tLevel = useTranslations("options.skill_level");
  const locale = useLocale();
  const [sessions, setSessions] = useState(initialSessions);
  const [role, setRole] = useState("");
  const [level, setLevel] = useState<Difficulty | "">("");
  const [starting, setStarting] = useState(false);

  async function start(e: React.FormEvent) {
    e.preventDefault();
    if (role.trim().length < 2) {
      toast.error(t("roleRequired"));
      return;
    }
    setStarting(true);
    try {
      const session = await startInterview(role.trim(), level || undefined);
      router.push(`/interview/${session.id}`);
    } catch (err) {
      toast.error(apiErrorMessage(err, t("startFailed")));
      setStarting(false);
    }
  }

  async function remove(id: string) {
    try {
      await deleteInterview(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
    } catch {
      toast.error(t("deleteFailed"));
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title={t("title")} subtitle={t("subtitle")} />

      <Card className="mt-6 p-6">
        <form onSubmit={start} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="role">{t("role")}</Label>
            <Input
              id="role"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder={t("roleExample")}
              maxLength={120}
            />
          </div>

          <FilterChips
            label={t("difficulty")}
            size="sm"
            value={level}
            onChange={setLevel}
            options={LEVELS.map((key) => ({ value: key, label: key ? tLevel(key) : t("levelAny") }))}
          />

          <LoadingButton type="submit" loading={starting} className="gap-2">
            <Mic size={15} /> {t("start")}
          </LoadingButton>
        </form>
      </Card>

      <h2 className="font-heading mt-10 text-lg font-semibold">
        {t("yours")}
      </h2>
      <Card className="mt-3 gap-0 p-0">
        {sessions.length === 0 ? (
          <p className="px-5 py-8 text-center text-sm text-muted-foreground">
            {t("none")}
          </p>
        ) : (
          sessions.map((s) => (
            <div
              key={s.id}
              className="flex items-center gap-3 border-b px-5 py-3.5 last:border-b-0"
            >
              <Link href={`/interview/${s.id}`} className="min-w-0 flex-1">
                <p className="truncate font-medium hover:text-brand-gold-deep dark:hover:text-brand-gold">
                  {s.role}
                </p>
                <p className="text-xs text-muted-foreground">
                  {t("answered", {
                    level: tLevel(s.difficulty),
                    answered: s.answered,
                    total: s.total,
                    date: formatDate(s.created_at, undefined, locale),
                  })}
                </p>
              </Link>
              <span
                className={cn(
                  "rounded-full px-2.5 py-0.5 text-xs font-medium",
                  s.status === "completed"
                    ? "bg-emerald-500/10 text-emerald-600"
                    : "bg-brand-gold/15 text-brand-gold"
                )}
              >
                {s.status === "completed"
                  ? `${Math.round(s.overall_score ?? 0)}%`
                  : t("inProgress")}
              </span>
              <button
                aria-label={t("delete", { role: s.role })}
                onClick={() => {
                  if (window.confirm(t("confirmDelete"))) remove(s.id);
                }}
                className="rounded-lg p-1.5 text-muted-foreground transition hover:text-destructive"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))
        )}
      </Card>
    </div>
  );
}
