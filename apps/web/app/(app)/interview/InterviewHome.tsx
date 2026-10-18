"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
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

const LEVELS: { key: Difficulty | ""; label: string }[] = [
  { key: "", label: "Match my level" },
  { key: "beginner", label: "Beginner" },
  { key: "intermediate", label: "Intermediate" },
  { key: "advanced", label: "Advanced" },
];

function errorMessage(error: unknown, fallback: string) {
  const detail = (error as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}

export default function InterviewHome({
  initialSessions,
}: {
  initialSessions: InterviewListItem[];
}) {
  const router = useRouter();
  const [sessions, setSessions] = useState(initialSessions);
  const [role, setRole] = useState("");
  const [level, setLevel] = useState<Difficulty | "">("");
  const [starting, setStarting] = useState(false);

  async function start(e: React.FormEvent) {
    e.preventDefault();
    if (role.trim().length < 2) {
      toast.error("Enter the role you are interviewing for.");
      return;
    }
    setStarting(true);
    try {
      const session = await startInterview(role.trim(), level || undefined);
      router.push(`/interview/${session.id}`);
    } catch (err) {
      toast.error(errorMessage(err, "Couldn't start the interview."));
      setStarting(false);
    }
  }

  async function remove(id: string) {
    try {
      await deleteInterview(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
    } catch {
      toast.error("Couldn't delete the interview.");
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="font-heading text-3xl font-bold">Interview Coach</h1>
      <p className="mt-1 text-muted-foreground">
        Practice with 5 questions for your target role and get scored feedback
        on each answer. This is text-only, so confidence is judged from your
        wording, not your voice.
      </p>

      <Card className="mt-6 p-6">
        <form onSubmit={start} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="role">Role you are interviewing for</Label>
            <Input
              id="role"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder="e.g. Junior Backend Developer"
              maxLength={120}
            />
          </div>

          <div className="flex flex-wrap gap-1.5">
            {LEVELS.map(({ key, label }) => (
              <button
                type="button"
                key={label}
                onClick={() => setLevel(key)}
                className={cn(
                  "rounded-full px-3 py-1 text-xs font-medium transition",
                  level === key
                    ? "bg-brand-violet text-white"
                    : "bg-muted text-muted-foreground hover:text-foreground"
                )}
              >
                {label}
              </button>
            ))}
          </div>

          <LoadingButton type="submit" loading={starting} className="gap-2">
            <Mic size={15} /> Start mock interview
          </LoadingButton>
        </form>
      </Card>

      <h2 className="font-heading mt-10 text-lg font-semibold">
        Your interviews
      </h2>
      <Card className="mt-3 gap-0 p-0">
        {sessions.length === 0 ? (
          <p className="px-5 py-8 text-center text-sm text-muted-foreground">
            No interviews yet.
          </p>
        ) : (
          sessions.map((s) => (
            <div
              key={s.id}
              className="flex items-center gap-3 border-b px-5 py-3.5 last:border-b-0"
            >
              <Link href={`/interview/${s.id}`} className="min-w-0 flex-1">
                <p className="truncate font-medium hover:text-brand-violet">
                  {s.role}
                </p>
                <p className="text-xs capitalize text-muted-foreground">
                  {s.difficulty} · {s.answered}/{s.total} answered ·{" "}
                  {formatDate(s.created_at)}
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
                  : "In progress"}
              </span>
              <button
                aria-label={`Delete interview for ${s.role}`}
                onClick={() => {
                  if (window.confirm("Delete this interview?")) remove(s.id);
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
