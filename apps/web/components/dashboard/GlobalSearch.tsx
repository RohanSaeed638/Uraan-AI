"use client";

import { useQuery } from "@tanstack/react-query";
import {
  BookOpen,
  Bot,
  CheckSquare,
  Compass,
  FileText,
  LayoutGrid,
  Library,
  Loader2,
  Search,
  Target,
  X,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useId, useMemo, useRef, useState, type ReactNode } from "react";

import { searchAll, type SearchHit, type SearchKind } from "@/lib/api/search";
import { cn } from "@/lib/utils";

import { NAV_ITEMS } from "./Sidebar";

const ICONS: Record<SearchKind | "page", typeof Search> = {
  page: LayoutGrid,
  roadmap: Target,
  task: CheckSquare,
  lesson: BookOpen,
  career: Compass,
  resource: Library,
  document: FileText,
  conversation: Bot,
};

const GROUP_ORDER: (SearchKind | "page")[] = [
  "page",
  "roadmap",
  "task",
  "lesson",
  "career",
  "resource",
  "document",
  "conversation",
];

const MIN_LENGTH = 2;

interface Option {
  key: string;
  kind: SearchKind | "page";
  title: string;
  subtitle: string | null;
  url: string;
}

/** The matched letters in bold, so people see why a result came up. */
function highlight(text: string, query: string): ReactNode {
  const needle = query.trim();
  const at = needle ? text.toLowerCase().indexOf(needle.toLowerCase()) : -1;

  if (at < 0) return text;

  return (
    <>
      {text.slice(0, at)}
      <mark className="rounded-sm bg-brand-violet/20 px-0.5 text-inherit">{text.slice(at, at + needle.length)}</mark>
      {text.slice(at + needle.length)}
    </>
  );
}

/**
 * The top-bar search. Typing looks through the learner's roadmaps, tasks,
 * lessons, documents and mentor chats, the careers and the resource library,
 * and offers the app's own pages by name. Pick a result with the mouse, or with
 * the arrow keys and Enter, and it opens.
 */
export default function GlobalSearch({
  autoFocus = false,
  onDone,
  className,
}: {
  autoFocus?: boolean;
  /** Called after a result is opened or the box is dismissed (used by the phone overlay). */
  onDone?: () => void;
  className?: string;
}) {
  const t = useTranslations("search");
  const tNav = useTranslations("nav");
  const router = useRouter();
  const listId = useId();

  const [value, setValue] = useState("");
  const [term, setTerm] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const root = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLInputElement>(null);

  // Ask only once the person pauses typing.
  useEffect(() => {
    const timer = setTimeout(() => setTerm(value.trim()), 250);

    return () => clearTimeout(timer);
  }, [value]);

  const enabled = term.length >= MIN_LENGTH;
  const query = useQuery({
    queryKey: ["search", term],
    queryFn: ({ signal }) => searchAll(term, signal),
    enabled,
    staleTime: 30_000,
    retry: false,
  });

  const options = useMemo<Option[]>(() => {
    if (!enabled) return [];

    const needle = term.toLowerCase();
    const pages = NAV_ITEMS.filter(({ key }) => tNav(key).toLowerCase().includes(needle))
      .slice(0, 3)
      .map(({ key, href }) => ({
        key: `page:${key}`,
        kind: "page" as const,
        title: tNav(key),
        subtitle: null,
        url: href,
      }));
    const hits = (query.data ?? []).map((hit: SearchHit) => ({
      key: `${hit.kind}:${hit.id}`,
      kind: hit.kind,
      title: hit.title,
      subtitle: hit.subtitle,
      url: hit.url,
    }));

    return [...pages, ...hits].sort((a, b) => GROUP_ORDER.indexOf(a.kind) - GROUP_ORDER.indexOf(b.kind));
  }, [enabled, term, query.data, tNav]);

  // A highlight that no longer points at anything (the list got shorter) counts as none.
  const activeIndex = active < options.length ? active : -1;

  // Click anywhere else, or tab away: close.
  useEffect(() => {
    function away(event: PointerEvent) {
      if (root.current && !root.current.contains(event.target as Node)) setOpen(false);
    }

    document.addEventListener("pointerdown", away);

    return () => document.removeEventListener("pointerdown", away);
  }, []);

  function choose(option: Option) {
    setOpen(false);
    setValue("");
    setTerm("");
    router.push(option.url);
    onDone?.();
  }

  function onKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();

      if (!options.length) return;

      setOpen(true);
      setActive(
        event.key === "ArrowDown"
          ? (activeIndex + 1) % options.length
          : (activeIndex <= 0 ? options.length : activeIndex) - 1
      );
    } else if (event.key === "Enter") {
      const chosen = options[activeIndex] ?? (options.length === 1 ? options[0] : undefined);

      if (chosen) {
        event.preventDefault();
        choose(chosen);
      }
    } else if (event.key === "Escape") {
      if (open) {
        setOpen(false);
      } else {
        setValue("");
        onDone?.();
      }
    }
  }

  const showPanel = open && enabled;
  const waiting = enabled && (query.isFetching || term !== value.trim()) && !query.data;

  return (
    <div ref={root} className={cn("relative w-full", className)} role="search">
      <Search
        className="pointer-events-none absolute start-3.5 top-1/2 -translate-y-1/2 text-muted-foreground"
        size={15}
        aria-hidden
      />
      <input
        ref={input}
        type="text"
        role="combobox"
        aria-label={t("label")}
        aria-expanded={showPanel}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={activeIndex >= 0 ? `${listId}-${activeIndex}` : undefined}
        autoComplete="off"
        autoFocus={autoFocus}
        placeholder={t("placeholder")}
        value={value}
        onChange={(event) => {
          setValue(event.target.value);
          setActive(-1);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
        className="h-9 w-full rounded-full border border-transparent bg-muted/60 ps-9 pe-9 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30"
      />
      {value && (
        <button
          type="button"
          aria-label={t("clear")}
          onClick={() => {
            setValue("");
            setTerm("");
            input.current?.focus();
          }}
          className="absolute end-2 top-1/2 flex size-6 -translate-y-1/2 items-center justify-center rounded-full text-muted-foreground hover:bg-accent"
        >
          <X size={14} aria-hidden />
        </button>
      )}

      {showPanel && (
        <div className="absolute inset-x-0 top-full z-50 mt-2 max-h-[70vh] overflow-y-auto rounded-2xl border border-border bg-popover p-2 shadow-xl">
          <ul id={listId} role="listbox" aria-label={t("results")}>
            {options.map((option, index) => {
              const Icon = ICONS[option.kind];
              const heading = index === 0 || options[index - 1].kind !== option.kind;

              return (
                <li key={option.key} role="presentation">
                  {heading && (
                    <p className="px-3 pb-1 pt-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      {option.kind === "page" ? t("pages") : t(`groups.${option.kind}`)}
                    </p>
                  )}
                  <div
                    id={`${listId}-${index}`}
                    role="option"
                    aria-selected={index === activeIndex}
                    onMouseEnter={() => setActive(index)}
                    onMouseDown={(event) => event.preventDefault()}
                    onClick={() => choose(option)}
                    className={cn(
                      "flex cursor-pointer items-center gap-3 rounded-xl px-3 py-2 text-sm",
                      index === activeIndex ? "bg-accent text-accent-foreground" : "hover:bg-accent/60"
                    )}
                  >
                    <Icon size={16} className="shrink-0 text-violet-700 dark:text-brand-violet-light" aria-hidden />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-medium">{highlight(option.title, term)}</span>
                      {option.subtitle && (
                        <span className="block truncate text-xs text-muted-foreground">{option.subtitle}</span>
                      )}
                    </span>
                  </div>
                </li>
              );
            })}
          </ul>

          <div role="status" aria-live="polite">
            {waiting && options.length === 0 && (
              <p className="flex items-center gap-2 px-3 py-3 text-sm text-muted-foreground">
                <Loader2 size={14} className="animate-spin" aria-hidden /> {t("searching")}
              </p>
            )}
            {query.isError && (
              <p className="px-3 py-3 text-sm text-destructive">{t("failed")}</p>
            )}
            {!waiting && !query.isError && query.isSuccess && options.length === 0 && (
              <p className="px-3 py-3 text-sm text-muted-foreground">{t("none", { query: term })}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
