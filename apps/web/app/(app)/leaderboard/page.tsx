import Link from "next/link";
import { Trophy } from "lucide-react";

import { getLeaderboard } from "@/lib/server/data";
import { LeaderboardPeriod } from "@/types/api";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const periods: { key: LeaderboardPeriod; label: string }[] = [
  { key: "weekly", label: "This week" },
  { key: "all_time", label: "All time" },
];

export default async function LeaderboardPage({
  searchParams,
}: {
  searchParams: Promise<{ period?: string }>;
}) {
  const { period: raw } = await searchParams;
  const period: LeaderboardPeriod = raw === "all_time" ? "all_time" : "weekly";

  const board = await getLeaderboard(period);

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="font-heading text-3xl font-bold">Leaderboard</h1>
      <p className="mt-1 text-muted-foreground">
        Top learners by XP. Only people who opted in appear here.
      </p>

      <div className="mt-6 flex gap-2">
        {periods.map(({ key, label }) => (
          <Link
            key={key}
            href={`/leaderboard?period=${key}`}
            className={cn(
              "rounded-full px-4 py-1.5 text-sm font-medium transition",
              period === key
                ? "bg-brand-violet text-white"
                : "bg-muted text-muted-foreground hover:text-foreground"
            )}
          >
            {label}
          </Link>
        ))}
      </div>

      {board && (
        <Card className="mt-6 gap-1 p-5">
          <p className="text-sm font-semibold">Your standing</p>
          {board.me.on_leaderboard ? (
            <p className="text-sm text-muted-foreground">
              {board.me.rank
                ? `Rank #${board.me.rank} with ${board.me.xp} XP.`
                : "Earn some XP this period to get ranked."}
            </p>
          ) : (
            <p className="text-sm text-muted-foreground">
              You have {board.me.xp} XP but you&apos;re hidden from the board.{" "}
              <Link
                href="/settings"
                className="font-medium text-brand-violet hover:underline"
              >
                Turn on leaderboard visibility
              </Link>{" "}
              in Settings to join.
            </p>
          )}
        </Card>
      )}

      {!board || board.entries.length === 0 ? (
        <div className="mx-auto mt-16 flex max-w-sm flex-col items-center text-center">
          <span className="flex size-16 items-center justify-center rounded-full bg-brand-violet/10">
            <Trophy className="size-7 text-brand-violet" />
          </span>
          <h2 className="font-heading mt-5 text-xl font-bold">
            No one is on the board yet
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Complete lessons, tasks and quizzes to earn XP and be the first.
          </p>
        </div>
      ) : (
        <Card className="mt-6 gap-0 p-0">
          {board.entries.map((entry) => (
            <div
              key={entry.rank}
              className={cn(
                "flex items-center gap-4 border-b border-border px-5 py-3.5 last:border-b-0",
                entry.is_me && "bg-brand-violet/5"
              )}
            >
              <span className="w-8 text-center text-sm font-bold text-muted-foreground">
                {entry.rank}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">
                  {entry.display_name}
                  {entry.is_me && (
                    <span className="ml-2 text-xs font-normal text-brand-violet">
                      you
                    </span>
                  )}
                </p>
                <p className="text-xs text-muted-foreground">
                  Level {entry.level}
                </p>
              </div>
              <span className="text-sm font-semibold">{entry.xp} XP</span>
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}
