import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ExternalLink } from "lucide-react";

import { PublicPortfolio } from "@/types/api";

import { Card } from "@/components/ui/card";

async function getPublicPortfolio(slug: string): Promise<PublicPortfolio | null> {
  try {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/portfolio/public/${encodeURIComponent(slug)}`,
      { cache: "no-store" }
    );
    return res.ok ? ((await res.json()) as PublicPortfolio) : null;
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const portfolio = await getPublicPortfolio(slug);

  return portfolio
    ? {
        title: `${portfolio.name} - Portfolio`,
        description: portfolio.headline ?? undefined,
      }
    : { title: "Portfolio not found" };
}

export default async function PublicPortfolioPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const portfolio = await getPublicPortfolio(slug);

  if (!portfolio) notFound();

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="font-heading text-4xl font-bold">{portfolio.name}</h1>
      {portfolio.headline && (
        <p className="mt-2 text-lg text-muted-foreground">
          {portfolio.headline}
        </p>
      )}
      {portfolio.bio && (
        <p className="mt-6 whitespace-pre-wrap leading-7">{portfolio.bio}</p>
      )}

      <h2 className="font-heading mt-12 text-2xl font-semibold">Projects</h2>
      {portfolio.projects.length === 0 ? (
        <p className="mt-3 text-muted-foreground">No projects to show yet.</p>
      ) : (
        <div className="mt-4 space-y-4">
          {portfolio.projects.map((p, i) => (
            <Card key={i} className="gap-3 p-6">
              <h3 className="text-lg font-semibold">{p.title}</h3>
              {p.description && (
                <p className="whitespace-pre-wrap text-sm leading-6 text-muted-foreground">
                  {p.description}
                </p>
              )}
              {p.tech.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {p.tech.map((t) => (
                    <span
                      key={t}
                      className="rounded-full bg-brand-violet/10 px-2.5 py-0.5 text-xs font-medium text-brand-violet"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              )}
              <div className="flex gap-4 text-sm font-medium">
                {p.repo_url && (
                  <a
                    href={p.repo_url}
                    target="_blank"
                    rel="noopener noreferrer nofollow"
                    className="flex items-center gap-1 text-brand-violet hover:underline"
                  >
                    Code <ExternalLink size={13} />
                  </a>
                )}
                {p.live_url && (
                  <a
                    href={p.live_url}
                    target="_blank"
                    rel="noopener noreferrer nofollow"
                    className="flex items-center gap-1 text-brand-violet hover:underline"
                  >
                    Live demo <ExternalLink size={13} />
                  </a>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      <p className="mt-16 text-center text-xs text-muted-foreground">
        Built with Uraan AI
      </p>
    </main>
  );
}
