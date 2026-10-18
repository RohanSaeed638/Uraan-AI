"use client";

import { useState, useSyncExternalStore } from "react";
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

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

function errorMessage(error: unknown, fallback: string) {
  const detail = (error as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg);
  return fallback;
}

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
      toast.success("Project saved.");
    } catch (e) {
      toast.error(errorMessage(e, "Couldn't save the project."));
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
      toast.success("Draft added. Edit it, then save.");
    } catch (e) {
      toast.error(errorMessage(e, "Couldn't write a draft right now."));
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
          aria-label="Project title"
          maxLength={160}
          className="font-medium"
        />
        <Button
          variant="ghost"
          size="icon"
          aria-label={`Delete ${project.title}`}
          onClick={() => {
            if (window.confirm(`Remove "${project.title}" from your portfolio?`)) {
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
        aria-label="Project description"
        placeholder="What does it do and what did you use?"
        maxLength={4000}
        className="min-h-20"
      />

      <div className="grid gap-3 sm:grid-cols-2">
        <Input
          value={repo}
          onChange={(e) => setRepo(e.target.value)}
          placeholder="https://github.com/you/project"
          aria-label="Repository link"
        />
        <Input
          value={live}
          onChange={(e) => setLive(e.target.value)}
          placeholder="https://your-demo.app"
          aria-label="Live demo link"
        />
      </div>
      <Input
        value={tech}
        onChange={(e) => setTech(e.target.value)}
        placeholder="Technologies, comma separated"
        aria-label="Technologies"
      />

      <div className="flex flex-wrap items-center gap-2">
        <Button size="sm" disabled={busy !== null} onClick={() => save()}>
          {busy === "save" ? "Saving…" : "Save"}
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="gap-2"
          disabled={busy !== null}
          onClick={draft}
        >
          <Sparkles size={14} /> {busy === "draft" ? "Writing…" : "Draft with AI"}
        </Button>
        <label className="ml-auto flex cursor-pointer items-center gap-2 text-xs text-muted-foreground">
          <input
            type="checkbox"
            className="size-4 accent-brand-violet"
            checked={project.visible}
            onChange={(e) => save({ visible: e.target.checked })}
          />
          Show on public page
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
  const [data, setData] = useState(initial);
  const [headline, setHeadline] = useState(initial?.headline ?? "");
  const [bio, setBio] = useState(initial?.bio ?? "");
  const [slug, setSlug] = useState(initial?.slug ?? "");
  const [busy, setBusy] = useState(false);
  const siteOrigin = useSyncExternalStore(noSubscription, origin, () => "");

  if (!data) {
    return (
      <p className="text-muted-foreground">
        Couldn&apos;t load your portfolio. Refresh the page to try again.
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
      toast.success("Portfolio saved.");
    } catch (e) {
      toast.error(errorMessage(e, "Couldn't save your portfolio."));
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
      toast.error(errorMessage(e, "Couldn't add the project."));
    }
  }

  async function toggleItem(id: string, done: boolean) {
    try {
      apply(await setChecklistItem(id, done));
    } catch {
      toast.error("Couldn't update the checklist.");
    }
  }

  const doneCount = data.checklist.filter((c) => c.done).length;

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div>
        <h1 className="font-heading text-3xl font-bold">Portfolio</h1>
        <p className="mt-1 text-muted-foreground">
          Showcase what you have built. It stays private until you publish it.
        </p>
      </div>

      <Card className="gap-4 p-6">
        <div className="space-y-1.5">
          <Label htmlFor="headline">Headline</Label>
          <Input
            id="headline"
            value={headline}
            onChange={(e) => setHeadline(e.target.value)}
            placeholder="Aspiring backend developer"
            maxLength={160}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="bio">About you</Label>
          <Textarea
            id="bio"
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            maxLength={2000}
            className="min-h-24"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="slug">Public address</Label>
          <div className="flex items-center gap-2">
            <span className="shrink-0 whitespace-nowrap text-sm text-muted-foreground">/p/</span>
            <Input
              id="slug"
              value={slug}
              onChange={(e) => setSlug(e.target.value.toLowerCase())}
              placeholder="auto-generated when you publish"
              maxLength={40}
            />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button disabled={busy} onClick={() => savePage()}>
            Save
          </Button>
          <Button
            variant={data.is_public ? "outline" : "default"}
            disabled={busy}
            onClick={() => savePage({ is_public: !data.is_public })}
          >
            {data.is_public ? "Make private" : "Publish"}
          </Button>
          {publicUrl && (
            <>
              <a
                href={publicUrl}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 text-sm font-medium text-brand-violet hover:underline"
              >
                View public page <ExternalLink size={13} />
              </a>
              <button
                aria-label="Copy public link"
                className="text-muted-foreground hover:text-foreground"
                onClick={() =>
                  navigator.clipboard
                    .writeText(publicUrl)
                    .then(() => toast.success("Link copied."))
                    .catch(() => toast.error("Couldn't copy."))
                }
              >
                <Copy size={14} />
              </button>
            </>
          )}
        </div>
        {data.is_public && (
          <p className="text-xs text-muted-foreground">
            Public pages show your name, headline, about text and the projects
            marked visible. Never your email.
          </p>
        )}
      </Card>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-xl font-semibold">Projects</h2>
          <Button
            size="sm"
            variant="outline"
            className="gap-2"
            onClick={() => addProject({ title: "New project" })}
          >
            <Plus size={14} /> Add project
          </Button>
        </div>

        {data.suggestions.length > 0 && (
          <Card className="gap-2 p-4">
            <p className="text-sm font-medium">
              From your completed roadmap projects
            </p>
            <div className="flex flex-wrap gap-2">
              {data.suggestions.map((s) => (
                <button
                  key={s.unit_id}
                  onClick={() =>
                    addProject({ source_unit_id: s.unit_id })
                  }
                  className="rounded-2xl bg-brand-violet/10 px-3 py-1.5 text-left text-xs font-medium text-brand-violet transition hover:bg-brand-violet/20"
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
            No projects yet. Add one above, or finish a project lesson in your
            roadmap and it will show up here.
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
                  toast.error("Couldn't remove the project.");
                }
              }}
            />
          ))
        )}
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-xl font-semibold">
            GitHub checklist
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
                className="mt-0.5 size-4 accent-brand-violet"
                checked={item.done}
                onChange={(e) => toggleItem(item.id, e.target.checked)}
              />
              <span
                className={cn(
                  "text-sm",
                  item.done && "text-muted-foreground line-through"
                )}
              >
                {item.label}
              </span>
              {item.done && (
                <Check size={14} className="ml-auto text-emerald-600" />
              )}
            </label>
          ))}
        </Card>
      </section>
    </div>
  );
}
