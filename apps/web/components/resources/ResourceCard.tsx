"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { Bookmark, ExternalLink, Share2, Star } from "lucide-react";

import {
  LibraryResource,
  setBookmark,
  setRating,
} from "@/lib/api/resources";
import { apiErrorMessage } from "@/lib/profile-options";
import { cn } from "@/lib/utils";

import Pill from "@/components/shared/Pill";
import { Card } from "@/components/ui/card";

interface Props {
  resource: LibraryResource;
  onChange: (resource: LibraryResource) => void;
  /** Compact: no rating row (used in small panels). */
  compact?: boolean;
}

export default function ResourceCard({ resource, onChange, compact }: Props) {
  const t = useTranslations("resources");
  const [busy, setBusy] = useState(false);

  async function run(action: () => Promise<LibraryResource>) {
    if (busy) return;
    setBusy(true);

    try {
      onChange(await action());
    } catch (err) {
      toast.error(apiErrorMessage(err, t("actionFailed")));
    } finally {
      setBusy(false);
    }
  }

  async function share() {
    const data = { title: resource.title, url: resource.url };

    try {
      if (typeof navigator.share === "function") {
        await navigator.share(data);
        return;
      }

      await navigator.clipboard.writeText(resource.url);
      toast.success(t("linkCopied"));
    } catch (err) {
      // Closing the share sheet is not an error.
      if ((err as Error)?.name !== "AbortError") toast.error(t("shareFailed"));
    }
  }

  return (
    <Card className="card-lift h-full gap-3 p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <a
            href={resource.url}
            target="_blank"
            rel="noopener noreferrer"
            className="line-clamp-2 font-heading font-semibold leading-snug hover:underline"
          >
            {resource.title}
          </a>
          {resource.provider && (
            <p className="mt-0.5 truncate text-xs text-muted-foreground">
              {resource.provider}
            </p>
          )}
        </div>

        <button
          type="button"
          aria-pressed={resource.bookmarked}
          aria-label={resource.bookmarked ? t("unsave") : t("save")}
          disabled={busy}
          onClick={() => run(() => setBookmark(resource.id, !resource.bookmarked))}
          className={cn(
            "shrink-0 rounded-full p-2 transition hover:bg-muted",
            resource.bookmarked ? "text-brand-violet" : "text-muted-foreground"
          )}
        >
          <Bookmark size={18} fill={resource.bookmarked ? "currentColor" : "none"} />
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        <Pill>{t(`types.${resource.type}`)}</Pill>
        {resource.difficulty && (
          <Pill className="capitalize">{t(`levels.${resource.difficulty}`)}</Pill>
        )}
        <Pill tone="soft">{resource.is_free ? t("free") : t("paid")}</Pill>
      </div>

      {!compact && (
        <div className="mt-auto flex flex-wrap items-center justify-between gap-2 pt-1">
          <div className="flex items-center gap-0.5" role="group" aria-label={t("yourRating")}>
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                type="button"
                disabled={busy}
                aria-label={t("rateStars", { count: n })}
                aria-pressed={resource.my_rating === n}
                onClick={() =>
                  run(() => setRating(resource.id, resource.my_rating === n ? null : n))
                }
                className="p-0.5 text-amber-500"
              >
                <Star
                  size={16}
                  fill={(resource.my_rating ?? 0) >= n ? "currentColor" : "none"}
                />
              </button>
            ))}
            <span className="ms-2 text-xs text-muted-foreground">
              {resource.avg_rating !== null
                ? t("average", { avg: resource.avg_rating, count: resource.rating_count })
                : t("noRatings")}
            </span>
          </div>

          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={share}
              aria-label={t("share")}
              className="rounded-full p-2 text-muted-foreground transition hover:bg-muted hover:text-foreground"
            >
              <Share2 size={16} />
            </button>
            <a
              href={resource.url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={t("open")}
              className="rounded-full p-2 text-muted-foreground transition hover:bg-muted hover:text-foreground"
            >
              <ExternalLink size={16} />
            </a>
          </div>
        </div>
      )}
    </Card>
  );
}
