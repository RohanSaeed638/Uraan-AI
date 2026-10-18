"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Copy, FileText, Printer, Save, Sparkles, Trash2 } from "lucide-react";
import { toast } from "sonner";

import {
  deleteDocument,
  generateDocument,
  updateDocument,
} from "@/lib/api/documents";
import { CareerDocument, DocumentKind } from "@/types/api";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import LoadingButton from "@/components/shared/LoadingButton";
import SimpleMarkdown from "@/components/shared/SimpleMarkdown";
import { cn } from "@/lib/utils";

const KINDS: { key: DocumentKind; label: string }[] = [
  { key: "resume", label: "Resume" },
  { key: "cover_letter", label: "Cover letter" },
  { key: "linkedin_summary", label: "LinkedIn summary" },
];

function errorMessage(error: unknown, fallback: string) {
  const detail = (error as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}

export default function ResumeClient({
  initialDocuments,
}: {
  initialDocuments: CareerDocument[];
}) {
  const [documents, setDocuments] = useState(initialDocuments);
  const [activeId, setActiveId] = useState<string | null>(
    initialDocuments[0]?.id ?? null
  );

  const [kind, setKind] = useState<DocumentKind>("resume");
  const [targetRole, setTargetRole] = useState("");
  const [details, setDetails] = useState("");
  const [jobDescription, setJobDescription] = useState("");

  const active = documents.find((d) => d.id === activeId) ?? null;
  const [draft, setDraft] = useState(active?.content ?? "");
  const [title, setTitle] = useState(active?.title ?? "");
  const [preview, setPreview] = useState(false);

  function select(doc: CareerDocument | null) {
    setActiveId(doc?.id ?? null);
    setDraft(doc?.content ?? "");
    setTitle(doc?.title ?? "");
    setPreview(false);
  }

  const generate = useMutation({
    mutationFn: generateDocument,
    onSuccess: (doc) => {
      setDocuments((prev) => [doc, ...prev]);
      select(doc);
      toast.success("Draft ready. Review it and fill in the [placeholders].");
    },
    onError: (e) =>
      toast.error(errorMessage(e, "Couldn't write the document. Try again.")),
  });

  const save = useMutation({
    mutationFn: () => updateDocument(active!.id, { title, content: draft }),
    onSuccess: (doc) => {
      setDocuments((prev) => prev.map((d) => (d.id === doc.id ? doc : d)));
      toast.success("Saved.");
    },
    onError: (e) => toast.error(errorMessage(e, "Couldn't save.")),
  });

  const remove = useMutation({
    mutationFn: (id: string) => deleteDocument(id),
    onSuccess: (_, id) => {
      const rest = documents.filter((d) => d.id !== id);
      setDocuments(rest);
      if (id === activeId) select(rest[0] ?? null);
    },
    onError: () => toast.error("Couldn't delete."),
  });

  const dirty = !!active && (draft !== active.content || title !== active.title);

  async function copy() {
    try {
      await navigator.clipboard.writeText(draft);
      toast.success("Copied.");
    } catch {
      toast.error("Couldn't copy. Select the text and copy it manually.");
    }
  }

  function onGenerate(e: React.FormEvent) {
    e.preventDefault();
    if (targetRole.trim().length < 2) {
      toast.error("Enter the role you are applying for.");
      return;
    }
    generate.mutate({
      kind,
      target_role: targetRole.trim(),
      details: details.trim(),
      job_description: jobDescription.trim(),
    });
  }

  return (
    <>
      <div className="mx-auto max-w-6xl print:hidden">
        <h1 className="font-heading text-3xl font-bold">Resume Builder</h1>
        <p className="mt-1 text-muted-foreground">
          Draft a resume, cover letter or LinkedIn summary from what you have
          actually completed. Nothing is invented: anything missing is left as
          a [placeholder] for you to fill in.
        </p>

        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[340px_minmax(0,1fr)]">
          <div className="min-w-0 space-y-6">
            <Card className="p-5">
              <form onSubmit={onGenerate} className="space-y-4">
                <div className="flex flex-wrap gap-1.5">
                  {KINDS.map(({ key, label }) => (
                    <button
                      type="button"
                      key={key}
                      onClick={() => setKind(key)}
                      className={cn(
                        "rounded-full px-3 py-1 text-xs font-medium transition",
                        kind === key
                          ? "bg-brand-violet text-white"
                          : "bg-muted text-muted-foreground hover:text-foreground"
                      )}
                    >
                      {label}
                    </button>
                  ))}
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="role">Target role</Label>
                  <Input
                    id="role"
                    value={targetRole}
                    onChange={(e) => setTargetRole(e.target.value)}
                    placeholder="e.g. Junior Backend Developer"
                    maxLength={120}
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="details">Your details (optional)</Label>
                  <Textarea
                    id="details"
                    value={details}
                    onChange={(e) => setDetails(e.target.value)}
                    placeholder="Education, experience, email, GitHub, LinkedIn…"
                    maxLength={4000}
                    className="min-h-24"
                  />
                </div>

                {kind === "cover_letter" && (
                  <div className="space-y-1.5">
                    <Label htmlFor="jd">Job description (optional)</Label>
                    <Textarea
                      id="jd"
                      value={jobDescription}
                      onChange={(e) => setJobDescription(e.target.value)}
                      placeholder="Paste the job posting to tailor the letter."
                      maxLength={6000}
                      className="min-h-24"
                    />
                  </div>
                )}

                <LoadingButton
                  type="submit"
                  loading={generate.isPending}
                  className="w-full gap-2"
                >
                  <Sparkles size={15} /> Write my {KINDS.find((k) => k.key === kind)!.label.toLowerCase()}
                </LoadingButton>
              </form>
            </Card>

            <Card className="gap-1 p-3">
              <p className="px-2 pt-1 text-sm font-semibold">Saved documents</p>
              {documents.length === 0 && (
                <p className="px-2 py-3 text-sm text-muted-foreground">
                  Nothing yet.
                </p>
              )}
              {documents.map((d) => (
                <div
                  key={d.id}
                  className={cn(
                    "group flex items-center gap-1 rounded-xl pr-1",
                    d.id === activeId
                      ? "bg-brand-violet/10 text-brand-violet"
                      : "hover:bg-muted"
                  )}
                >
                  <button
                    onClick={() => select(d)}
                    className="min-w-0 flex-1 truncate px-2 py-2 text-left text-sm font-medium"
                  >
                    {d.title}
                  </button>
                  <button
                    aria-label={`Delete ${d.title}`}
                    onClick={() => {
                      if (window.confirm(`Delete "${d.title}"?`)) {
                        remove.mutate(d.id);
                      }
                    }}
                    className="rounded-lg p-1.5 text-muted-foreground opacity-0 transition hover:text-destructive group-hover:opacity-100 focus:opacity-100"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </Card>
          </div>

          <Card className="min-h-[28rem] gap-4 p-5">
            {!active ? (
              <div className="flex flex-1 flex-col items-center justify-center text-center">
                <span className="flex size-14 items-center justify-center rounded-full bg-brand-violet/10">
                  <FileText className="size-6 text-brand-violet" />
                </span>
                <p className="mt-4 text-sm text-muted-foreground">
                  Generate a document to edit it here.
                </p>
              </div>
            ) : (
              <>
                <div className="flex flex-wrap items-center gap-2">
                  <Input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    aria-label="Document title"
                    maxLength={200}
                    className="min-w-48 flex-1 font-medium"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPreview((v) => !v)}
                  >
                    {preview ? "Edit" : "Preview"}
                  </Button>
                  <Button variant="outline" size="sm" className="gap-2" onClick={copy}>
                    <Copy size={14} /> Copy
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-2"
                    onClick={() => window.print()}
                  >
                    <Printer size={14} /> Print / PDF
                  </Button>
                  <Button
                    size="sm"
                    className="gap-2"
                    disabled={!dirty || save.isPending || !draft.trim() || !title.trim()}
                    onClick={() => save.mutate()}
                  >
                    <Save size={14} /> {save.isPending ? "Saving…" : "Save"}
                  </Button>
                </div>

                {preview ? (
                  <div className="rounded-2xl border bg-background p-6">
                    <SimpleMarkdown source={draft} />
                  </div>
                ) : (
                  <Textarea
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    aria-label="Document content"
                    maxLength={30000}
                    className="min-h-[24rem] font-mono text-sm"
                  />
                )}
                <p className="text-xs text-muted-foreground">
                  AI drafts can contain mistakes. Check every fact and replace
                  each [placeholder] before sending.
                </p>
              </>
            )}
          </Card>
        </div>
      </div>

      {/* Only this is shown when printing or saving as PDF. */}
      <div className="hidden print:block">
        <SimpleMarkdown source={draft} />
      </div>
    </>
  );
}
