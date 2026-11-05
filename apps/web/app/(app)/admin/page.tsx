import { getTranslations } from "next-intl/server";
import { Activity, BookOpenCheck, CheckSquare, MessageSquare, Target, UserPlus, Users } from "lucide-react";

import { getAdminStats } from "@/lib/server/data";

import EmptyState from "@/components/shared/EmptyState";
import StatTile from "@/components/shared/StatTile";
import { Card } from "@/components/ui/card";

export default async function AdminOverview() {
  const t = await getTranslations("admin.overview");
  const stats = await getAdminStats();

  if (!stats) {
    return <EmptyState icon={Activity} title={t("failed")} />;
  }

  const c = stats.counts;
  const rate = (failures: number, requests: number) =>
    requests === 0 ? "0%" : `${Math.round((failures / requests) * 100)}%`;

  return (
    <div className="space-y-8">
      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatTile icon={Users} value={c.users} label={t("users")} />
        <StatTile icon={UserPlus} value={c.new_users_7d} label={t("newUsers", { days: stats.days })} tone="green" />
        <StatTile icon={Activity} value={c.active_users_7d} label={t("activeUsers", { days: stats.days })} tone="sky" />
        <StatTile icon={Target} value={c.roadmaps} label={t("roadmaps")} tone="violet" />
        <StatTile icon={BookOpenCheck} value={c.lessons_completed} label={t("lessons")} />
        <StatTile icon={CheckSquare} value={c.tasks_completed} label={t("tasks")} tone="green" />
        <StatTile icon={MessageSquare} value={c.mentor_messages} label={t("messages")} tone="sky" />
      </section>

      <section>
        <h2 className="font-heading text-lg font-semibold">{t("aiTitle", { days: stats.days })}</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          {t("aiSummary", {
            requests: stats.ai_requests,
            failures: stats.ai_failures,
            rate: rate(stats.ai_failures, stats.ai_requests),
          })}
        </p>

        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          <Card className="overflow-x-auto p-0">
            <table className="w-full min-w-[420px] text-sm">
              <thead>
                <tr className="border-b text-start text-xs text-muted-foreground">
                  <th className="p-3 text-start font-medium">{t("purpose")}</th>
                  <th className="p-3 text-end font-medium">{t("requests")}</th>
                  <th className="p-3 text-end font-medium">{t("failureRate")}</th>
                  <th className="p-3 text-end font-medium">{t("latency")}</th>
                </tr>
              </thead>
              <tbody>
                {stats.ai_by_purpose.map((row) => (
                  <tr key={row.purpose} className="border-b last:border-0">
                    <td className="p-3 font-medium">{row.purpose}</td>
                    <td className="p-3 text-end">{row.requests}</td>
                    <td className="p-3 text-end">
                      <span className={row.failures > 0 ? "text-destructive" : ""}>
                        {rate(row.failures, row.requests)}
                      </span>
                    </td>
                    <td className="p-3 text-end text-muted-foreground">
                      {row.avg_latency_ms === null ? "-" : `${row.avg_latency_ms} ms`}
                    </td>
                  </tr>
                ))}
                {stats.ai_by_purpose.length === 0 && (
                  <tr>
                    <td colSpan={4} className="p-6 text-center text-muted-foreground">
                      {t("noAi")}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </Card>

          <Card className="gap-3 p-4">
            <p className="text-sm font-semibold">{t("providers")}</p>
            {stats.ai_by_provider.map((p) => (
              <div key={p.provider} className="flex items-center justify-between text-sm">
                <span className="font-medium">{p.provider}</span>
                <span className="text-muted-foreground">
                  {t("providerLine", { requests: p.requests, failures: p.failures })}
                </span>
              </div>
            ))}
            {stats.ai_by_provider.length === 0 && (
              <p className="text-sm text-muted-foreground">{t("noAi")}</p>
            )}
          </Card>
        </div>
      </section>

      <section>
        <h2 className="font-heading text-lg font-semibold">{t("failuresTitle")}</h2>
        <Card className="mt-3 gap-0 p-0">
          {stats.recent_failures.length === 0 ? (
            <p className="p-6 text-center text-sm text-muted-foreground">{t("noFailures")}</p>
          ) : (
            stats.recent_failures.map((f, i) => (
              <div key={i} className="flex flex-wrap items-center justify-between gap-2 border-b px-4 py-3 text-sm last:border-0">
                <span>
                  <span className="font-medium">{f.purpose}</span>
                  <span className="text-muted-foreground"> · {f.provider}</span>
                </span>
                <span className="text-xs text-muted-foreground">
                  {f.error_type ?? t("unknownError")} · {new Date(f.at).toISOString().replace("T", " ").slice(0, 16)} UTC
                </span>
              </div>
            ))
          )}
        </Card>
      </section>
    </div>
  );
}
