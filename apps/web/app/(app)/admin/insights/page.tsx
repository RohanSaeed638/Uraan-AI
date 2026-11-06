"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useState } from "react";

import {
  getAiUsage,
  getFeedbackOverview,
  getFunnel,
  getLinkOverview,
  type FunnelStep,
} from "@/lib/api/insights";

import EmptyState from "@/components/shared/EmptyState";
import FilterChips from "@/components/shared/FilterChips";
import { Card } from "@/components/ui/card";
import { BarChart3 } from "lucide-react";

const PERIODS = ["7", "30", "90"] as const;

const number = (n: number | null | undefined) => (n === null || n === undefined ? "-" : n.toLocaleString("en-US"));
const percent = (n: number | null | undefined) => (n === null || n === undefined ? "-" : `${n}%`);
const money = (n: number | null | undefined) => (n === null || n === undefined ? "unpriced" : `$${n.toFixed(2)}`);

function Section({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <div>
        <h2 className="font-heading text-lg font-semibold">{title}</h2>
        {hint && <p className="mt-1 text-sm text-muted-foreground">{hint}</p>}
      </div>
      {children}
    </section>
  );
}

function Stat({ label, value, sub }: { label: string; value: React.ReactNode; sub?: string }) {
  return (
    <Card className="gap-1 p-4">
      <p className="num text-2xl font-bold leading-none">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
      {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
    </Card>
  );
}

function Failed({ text }: { text: string }) {
  return <EmptyState icon={BarChart3} title={text} />;
}

/** How new learners move through the product. */
function FunnelSection() {
  const t = useTranslations("admin.insights");
  const query = useQuery({ queryKey: ["admin", "funnel"], queryFn: () => getFunnel(8), retry: false });

  if (query.isError) return <Failed text={t("failed")} />;
  if (!query.data) return null;

  const top = Math.max(1, query.data.steps[0]?.count ?? 1);

  return (
    <Section title={t("funnelTitle")} hint={t("funnelHint")}>
      <Card className="gap-4 p-5">
        {query.data.steps.map((step: FunnelStep) => (
          <div key={step.key}>
            <div className="mb-1 flex items-baseline justify-between gap-3 text-sm">
              <span className="font-medium">{t(`steps.${step.key}`)}</span>
              <span className="num text-muted-foreground">
                {number(step.count)}
                {step.of_signups !== null && ` - ${percent(step.of_signups)}`}
                {step.key === "returned" && ` ${t("ofEligible", { count: query.data.eligible_for_return })}`}
              </span>
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-gradient-to-r from-violet-500 to-indigo-600"
                style={{ width: `${Math.max(2, Math.round((step.count / top) * 100))}%` }}
              />
            </div>
          </div>
        ))}
      </Card>

      {query.data.cohorts.length > 0 && (
        <Card className="overflow-x-auto p-0">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b text-left text-xs text-muted-foreground">
                <th className="px-4 py-3 font-medium">{t("week")}</th>
                {(["signups", "onboarded", "roadmap", "first_lesson", "returned", "finished"] as const).map((k) => (
                  <th key={k} className="px-3 py-3 text-right font-medium">{t(`steps.${k}`)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {query.data.cohorts.map((c) => (
                <tr key={c.week} className="border-b last:border-0">
                  <td className="num px-4 py-2.5">{c.week}</td>
                  <td className="num px-3 py-2.5 text-right">{c.signups}</td>
                  <td className="num px-3 py-2.5 text-right">{c.onboarded}</td>
                  <td className="num px-3 py-2.5 text-right">{c.roadmap}</td>
                  <td className="num px-3 py-2.5 text-right">{c.first_lesson}</td>
                  <td className="num px-3 py-2.5 text-right">
                    {c.eligible_for_return ? `${c.returned}/${c.eligible_for_return}` : "-"}
                  </td>
                  <td className="num px-3 py-2.5 text-right">{c.finished}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </Section>
  );
}

/** Whether lessons help, and which topics and careers get marked down. */
function QualitySection({ days }: { days: number }) {
  const t = useTranslations("admin.insights");
  const query = useQuery({ queryKey: ["admin", "feedback", days], queryFn: () => getFeedbackOverview(days), retry: false });

  if (query.isError) return <Failed text={t("failed")} />;
  if (!query.data) return null;

  const d = query.data;

  return (
    <Section title={t("qualityTitle")} hint={t("qualityHint")}>
      <div className="grid gap-3 sm:grid-cols-3">
        <Stat label={t("votes")} value={number(d.total)} />
        <Stat label={t("helpfulShare")} value={percent(d.helpful_percent)} />
        <Stat label={t("notHelpful")} value={number(d.not_helpful)} />
      </div>

      {d.total === 0 ? (
        <p className="text-sm text-muted-foreground">{t("noVotes")}</p>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="gap-3 p-5">
            <p className="text-sm font-semibold">{t("whyMarkedDown")}</p>
            {d.by_reason.length === 0 ? (
              <p className="text-sm text-muted-foreground">-</p>
            ) : (
              d.by_reason.map((r) => (
                <div key={r.reason} className="flex justify-between text-sm">
                  <span>{t(`reasons.${r.reason}`)}</span>
                  <span className="num text-muted-foreground">{r.count}</span>
                </div>
              ))
            )}
          </Card>

          <Card className="gap-3 p-5">
            <p className="text-sm font-semibold">{t("byCareer")}</p>
            {d.by_career.map((c) => (
              <div key={c.career_slug} className="flex justify-between gap-3 text-sm">
                <span className="truncate">{c.career_slug}</span>
                <span className="num shrink-0 text-muted-foreground">
                  {percent(c.helpful_percent)} ({c.helpful + c.not_helpful})
                </span>
              </div>
            ))}
          </Card>

          <Card className="gap-3 p-5">
            <p className="text-sm font-semibold">{t("topics")}</p>
            {d.topics.length === 0 ? (
              <p className="text-sm text-muted-foreground">-</p>
            ) : (
              d.topics.map((topic) => (
                <div key={`${topic.task_title}-${topic.career_slug}`} className="flex justify-between gap-3 text-sm">
                  <span className="min-w-0 truncate">
                    {topic.task_title} <span className="text-muted-foreground">{topic.career_slug}</span>
                  </span>
                  <span className="num shrink-0 text-muted-foreground">
                    {topic.not_helpful} / {topic.helpful + topic.not_helpful}
                  </span>
                </div>
              ))
            )}
          </Card>

          <Card className="gap-3 p-5">
            <p className="text-sm font-semibold">{t("recentComments")}</p>
            {d.recent.length === 0 ? (
              <p className="text-sm text-muted-foreground">-</p>
            ) : (
              d.recent.slice(0, 8).map((r, i) => (
                <div key={i} className="border-b pb-2 text-sm last:border-0 last:pb-0">
                  <p className="font-medium">{r.lesson_title ?? r.task_title}</p>
                  <p className="text-xs text-muted-foreground">
                    {r.career_slug} - {r.reason ? t(`reasons.${r.reason}`) : t("noReason")}
                  </p>
                  {r.comment && <p className="mt-1 break-words text-muted-foreground">{r.comment}</p>}
                </div>
              ))
            )}
          </Card>
        </div>
      )}
    </Section>
  );
}

/** AI calls, tokens and an estimated bill. */
function UsageSection({ days }: { days: number }) {
  const t = useTranslations("admin.insights");
  const query = useQuery({ queryKey: ["admin", "ai-usage", days], queryFn: () => getAiUsage(days), retry: false });

  if (query.isError) return <Failed text={t("failed")} />;
  if (!query.data) return null;

  const d = query.data;
  const peak = Math.max(1, ...d.daily.map((x) => x.tokens));

  return (
    <Section title={t("usageTitle")} hint={t("usageHint")}>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label={t("requests")} value={number(d.requests)} sub={t("failedCount", { count: d.failed })} />
        <Stat label={t("tokens")} value={number(d.input_tokens + d.output_tokens)} sub={`${number(d.input_tokens)} in / ${number(d.output_tokens)} out`} />
        <Stat
          label={t("estimatedCost")}
          value={money(d.estimated_cost_usd)}
          sub={d.unpriced_tokens ? t("unpriced", { count: d.unpriced_tokens }) : undefined}
        />
        <Stat
          label={t("dailyLimit")}
          value={d.daily_limit_per_user ? number(d.daily_limit_per_user) : t("off")}
          sub={d.users_over_limit_today !== null ? t("overLimit", { count: d.users_over_limit_today }) : undefined}
        />
      </div>

      {d.daily.length > 0 && (
        <Card className="p-5">
          <p className="mb-3 text-sm font-semibold">{t("perDay")}</p>
          <div className="flex h-28 items-end gap-1" role="img" aria-label={t("perDay")}>
            {d.daily.map((day) => (
              <div
                key={day.date}
                title={`${day.date}: ${number(day.tokens)} tokens`}
                className="flex-1 rounded-t bg-gradient-to-t from-violet-600 to-indigo-400"
                style={{ height: `${Math.max(3, Math.round((day.tokens / peak) * 100))}%` }}
              />
            ))}
          </div>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="gap-3 p-5">
          <p className="text-sm font-semibold">{t("byModel")}</p>
          {d.by_model.map((m) => (
            <div key={`${m.provider}-${m.model}`} className="flex justify-between gap-3 text-sm">
              <span className="min-w-0 truncate">{m.provider} / {m.model}</span>
              <span className="num shrink-0 text-muted-foreground">
                {number(m.requests)} - {money(m.estimated_cost_usd)}
              </span>
            </div>
          ))}
        </Card>

        <Card className="gap-3 p-5">
          <p className="text-sm font-semibold">{t("byFeature")}</p>
          {d.by_purpose.map((p) => (
            <div key={p.purpose} className="flex justify-between text-sm">
              <span>{p.purpose}</span>
              <span className="num text-muted-foreground">{number(p.tokens)}</span>
            </div>
          ))}
        </Card>

        <Card className="gap-3 p-5 lg:col-span-2">
          <p className="text-sm font-semibold">{t("heaviest")}</p>
          {d.top_users.map((u) => (
            <div key={u.profile_id} className="flex justify-between text-sm">
              <span className="truncate">{u.name}</span>
              <span className="num text-muted-foreground">{number(u.tokens)} tokens, {number(u.requests)} calls</span>
            </div>
          ))}
        </Card>
      </div>
    </Section>
  );
}

/** Broken learning links found by the weekly checker. */
function LinksSection() {
  const t = useTranslations("admin.insights");
  const query = useQuery({ queryKey: ["admin", "links"], queryFn: getLinkOverview, retry: false });

  if (query.isError) return <Failed text={t("failed")} />;
  if (!query.data) return null;

  const d = query.data;

  return (
    <Section title={t("linksTitle")} hint={t("linksHint")}>
      <div className="grid gap-3 sm:grid-cols-4">
        <Stat label={t("linksOk")} value={number(d.ok)} />
        <Stat label={t("linksDead")} value={number(d.dead)} />
        <Stat label={t("linksUnknown")} value={number(d.unknown)} />
        <Stat label={t("lastChecked")} value={d.last_checked ? d.last_checked.slice(0, 10) : "-"} />
      </div>

      {d.dead_links.length > 0 && (
        <Card className="gap-0 p-0">
          {d.dead_links.map((link) => (
            <div key={link.url} className="space-y-0.5 border-b px-4 py-3 text-sm last:border-0">
              <p className="break-all font-medium">{link.url}</p>
              <p className="text-xs text-muted-foreground">
                {link.http_status ?? "-"} - {link.reason} - {t("failedChecks", { count: link.fail_count })}
              </p>
            </div>
          ))}
        </Card>
      )}
    </Section>
  );
}

export default function AdminInsightsPage() {
  const t = useTranslations("admin.insights");
  const [period, setPeriod] = useState<(typeof PERIODS)[number]>("30");

  return (
    <div className="space-y-10">
      <p className="text-sm text-muted-foreground">{t("intro")}</p>

      <FunnelSection />

      <FilterChips
        label={t("period")}
        size="sm"
        value={period}
        onChange={setPeriod}
        options={PERIODS.map((p) => ({ value: p, label: t("lastDays", { count: Number(p) }) }))}
      />

      <QualitySection days={Number(period)} />
      <UsageSection days={Number(period)} />
      <LinksSection />
    </div>
  );
}
