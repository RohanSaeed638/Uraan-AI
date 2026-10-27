"use client";

import { useState, useSyncExternalStore } from "react";
import { useTranslations } from "next-intl";
import PageHeader from "@/components/shared/PageHeader";
import { Check, Copy, ExternalLink, Plus, Sparkles, Trash2 } from "lucide-react";
import { toast } from "sonner";

import {
  createProject,
  deleteProject,
  draftProjectDescription,
  ProjectInput,
  setChecklistItem,
  updatePortfolio,
  updateProject,
} from "@/lib/api/portfolio";
import { Portfolio, PortfolioProject } from "@/types/api";
import { apiErrorMessage } from "@/lib/profile-options";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

const origin = () => window.location.origin;
const noSubscription = () => () => {};

function ProjectCard({
  project,
  onChange,
  onDelete,
}: {
  project: PortfolioProject;
  onChange: (p: PortfolioProject) => void;
  onDelete: (id: string) => void;
}) {
  const t = useTranslations("portfolio.card");
  const [title, setTitle] = useState(project.title);
  const [description, setDescription] = useState(project.description ?? "");
  const [repo, setRepo] = useState(project.repo_url ?? "");
  const [live, setLive] = useState(project.live_url ?? "");
  const [tech, setTech] = useState(project.tech.join(", "));
  const [busy, setBusy] = useState<"save" | "draft" | null>(null);

  async function save(extra: ProjectInput = {}) {
    setBusy("save");
    try {
      const updated = await updateProject(project.id, {
        title,
        description,
        repo_url: repo,
        live_url: live,
        tech: tech.split(",").map((t) => t.trim()).filter(Boolean),
        ...extra,
      });
      onChange(updated);
      toast.success(t("saved"));
    } catch (e) {
      toast.error(apiErrorMessage(e, t("saveFailed")));
    } finally {
      setBusy(null);
    }
  }

  async function draft() {
    setBusy("draft");
    try {
      // Saves current fields first so the draft sees the latest tech list.
      await save();
      setDescription(await draftProjectDescription(project.id));
      toast.success(t("drafted"));
    } catch (e) {
      toast.error(apiErrorMessage(e, t("draftFailed")));
    } finally {
      setBusy(null);
    }
  }

  return (
    <Card className="gap-3 p-5">
      <div className="flex items-start gap-2">
        <Input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          aria-label={t("title")}
          maxLength={160}
          className="font-medium"
        />
        <Button
          variant="ghost"
          size="icon"
          aria-label={t("delete", { title: project.title })}
          onClick={() => {
            if (window.confirm(t("confirmDelete", { title: project.title }))) {
              onDelete(project.id);
            }
          }}
        >
          <Trash2 size={15} />
        </Button>
      </div>

      <Textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        aria-label={t("description")}
        placeholder={t("descriptionHint")}
        maxLength={4000}
        className="min-h-20"
      />

      <div className="grid gap-3 sm:grid-cols-2">
        <Input
          value={repo}
          onChange={(e) => setRepo(e.target.value)}
          placeholder="https://github.com/you/project"
          aria-label={t("repo")}
        />
        <Input
          value={live}
          onChange={(e) => setLive(e.target.value)}
          placeholder="https://your-demo.app"
          aria-label={t("live")}
        />
      </div>
      <Input
        value={tech}
        onChange={(e) => setTech(e.target.value)}
        placeholder={t("techHint")}
        aria-label={t("tech")}
      />

      <div className="flex flex-wrap items-center gap-2">
        <Button size="sm" disabled={busy !== null} onClick={() => save()}>
          {busy === "save" ? t("saving") : t("save")}
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="gap-2"
          disabled={busy !== null}
          onClick={draft}
        >
          <Sparkles size={14} /> {busy === "draft" ? t("writing") : t("draft")}
        </Button>
        <label className="ms-auto flex cursor-pointer items-center gap-2 text-xs text-muted-foreground">
          <input
            type="checkbox"
            className="size-4 accent-gold"
            checked={project.visible}
            onChange={(e) => save({ visible: e.target.checked })}
          />
          {t("visible")}
        </label>
      </div>
    </Card>
  );
}

export default function PortfolioClient({
  initial,
}: {
  initial: Portfolio | null;
}) {
  const t = useTranslations("portfolio");
  const [data, setData] = useState(initial);
  const [headline, setHeadline] = useState(initial?.headline ?? "");
  const [bio, setBio] = useState(initial?.bio ?? "");
  const [slug, setSlug] = useState(initial?.slug ?? "");
  const [busy, setBusy] = useState(false);
  const siteOrigin = useSyncExternalStore(noSubscription, origin, () => "");

  if (!data) {
    return (
      <p className="text-muted-foreground">
        {t("loadFailed")}
      </p>
    );
  }

  const publicUrl =
    data.is_public && data.slug ? `${siteOrigin}/p/${data.slug}` : null;

  function apply(next: Portfolio) {
    setData(next);
    setSlug(next.slug ?? "");
  }

  async function savePage(extra: { is_public?: boolean } = {}) {
    setBusy(true);
    try {
      apply(
        await updatePortfolio({
          headline,
          bio,
          ...(slug && slug !== data!.slug ? { slug } : {}),
          ...extra,
        })
      );
      toast.success(t("saved"));
    } catch (e) {
      toast.error(apiErrorMessage(e, t("saveFailed")));
    } finally {
      setBusy(false);
    }
  }

  async function addProject(input: ProjectInput & { source_unit_id?: string }) {
    try {
      const created = await createProject(input);
      setData((prev) =>
        prev
          ? {
              ...prev,
              projects: [...prev.projects, created],
              suggestions: prev.suggestions.filter(
                (s) => s.unit_id !== input.source_unit_id
              ),
            }
          : prev
      );
    } catch (e) {
      toast.error(apiErrorMessage(e, t("addFailed")));
    }
  }

  async function toggleItem(id: string, done: boolean) {
    try {
      apply(await setChecklistItem(id, done));
    } catch {
      toast.error(t("checklistFailed"));
    }
  }

  const doneCount = data.checklist.filter((c) => c.done).length;

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <PageHeader title={t("title")} subtitle={t("subtitle")} />

      <Card className="gap-4 p-6">
        <div className="space-y-1.5">
          <Label htmlFor="headline">{t("headline")}</Label>
          <Input
            id="headline"
            value={headline}
            onChange={(e) => setHeadline(e.target.value)}
            placeholder={t("headlineExample")}
            maxLength={160}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="bio">{t("about")}</Label>
          <Textarea
            id="bio"
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            maxLength={2000}
            className="min-h-24"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="slug">{t("address")}</Label>
          <div className="flex items-center gap-2">
            <span dir="ltr" className="shrink-0 whitespace-nowrap text-sm text-muted-foreground">/p/</span>
            <Input
              id="slug"
              value={slug}
              onChange={(e) => setSlug(e.target.value.toLowerCase())}
              placeholder={t("addressHint")}
              maxLength={40}
            />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button disabled={busy} onClick={() => savePage()}>
            {t("save")}
          </Button>
          <Button
            variant={data.is_public ? "outline" : "default"}
            disabled={busy}
            onClick={() => savePage({ is_public: !data.is_public })}
          >
            {data.is_public ? t("makePrivate") : t("publish")}
          </Button>
          {publicUrl && (
            <>
              <a
                href={publicUrl}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 text-sm font-medium text-brand-gold-deep dark:text-brand-gold hover:underline"
              >
                {t("view")} <ExternalLink size={13} />
              </a>
              <button
                aria-label={t("copyLink")}
                className="text-muted-foreground hover:text-foreground"
                onClick={() =>
                  navigator.clipboard
                    .writeText(publicUrl)
                    .then(() => toast.success(t("copied")))
                    .catch(() => toast.error(t("copyFailed")))
                }
              >
                <Copy size={14} />
              </button>
            </>
          )}
        </div>
        {data.is_public && (
          <p className="text-xs text-muted-foreground">
            {t("publicNote")}
          </p>
        )}
      </Card>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-xl font-semibold">{t("projects")}</h2>
          <Button
            size="sm"
            variant="outline"
            className="gap-2"
            onClick={() => addProject({ title: t("newProject") })}
          >
            <Plus size={14} /> {t("addProject")}
          </Button>
        </div>

        {data.suggestions.length > 0 && (
          <Card className="gap-2 p-4">
            <p className="text-sm font-medium">
              {t("fromRoadmap")}
            </p>
            <div className="flex flex-wrap gap-2">
              {data.suggestions.map((s) => (
                <button
                  key={s.unit_id}
                  onClick={() =>
                    addProject({ source_unit_id: s.unit_id })
                  }
                  className="rounded-2xl bg-brand-violet/10 px-3 py-1.5 text-start text-xs font-medium text-brand-violet transition hover:bg-brand-violet/20"
                  title={s.task_title}
                >
                  + {s.title}
                </button>
              ))}
            </div>
          </Card>
        )}

        {data.projects.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {t("noProjects")}
          </p>
        ) : (
          data.projects.map((p) => (
            <ProjectCard
              key={p.id}
              project={p}
              onChange={(updated) =>
                setData((prev) =>
                  prev
                    ? {
                        ...prev,
                        projects: prev.projects.map((x) =>
                          x.id === updated.id ? updated : x
                        ),
                      }
                    : prev
                )
              }
              onDelete={async (id) => {
                try {
                  await deleteProject(id);
                  setData((prev) =>
                    prev
                      ? {
                          ...prev,
                          projects: prev.projects.filter((x) => x.id !== id),
                        }
                      : prev
                  );
                } catch {
                  toast.error(t("removeFailed"));
                }
              }}
            />
          ))
        )}
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-xl font-semibold">
            {t("github")}
          </h2>
          <span className="text-sm text-muted-foreground">
            {doneCount}/{data.checklist.length}
          </span>
        </div>
        <Card className="gap-0 p-0">
          {data.checklist.map((item) => (
            <label
              key={item.id}
              className="flex cursor-pointer items-start gap-3 border-b px-5 py-3.5 last:border-b-0"
            >
              <input
                type="checkbox"
                className="mt-0.5 size-4 accent-gold"
                checked={item.done}
                onChange={(e) => toggleItem(item.id, e.target.checked)}
              />
              <span
                className={cn(
                  "text-sm",
                  item.done && "text-muted-foreground line-through"
                )}
              >
                {t.has(`checklist.${item.id}`) ? t(`checklist.${item.id}`) : item.label}
              </span>
              {item.done && (
                <Check size={14} className="ms-auto text-emerald-600" />
              )}
            </label>
          ))}
        </Card>
      </section>
    </div>
  );
}
