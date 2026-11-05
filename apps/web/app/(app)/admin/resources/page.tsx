"use client";

import { useState } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { BookOpen, Pencil, Plus } from "lucide-react";
import { toast } from "sonner";

import {
  AdminResource,
  ResourceInput,
  createResource,
  listAdminResources,
  updateResource,
} from "@/lib/api/admin";
import { apiErrorMessage } from "@/lib/profile-options";

import EmptyState from "@/components/shared/EmptyState";
import FilterChips from "@/components/shared/FilterChips";
import LoadingButton from "@/components/shared/LoadingButton";
import NativeSelect from "@/components/shared/NativeSelect";
import Pill from "@/components/shared/Pill";
import SearchField from "@/components/shared/SearchField";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

const PAGE = 25;
const TYPES = ["course", "video", "docs", "book", "practice"];
const LEVELS = ["beginner", "intermediate", "advanced"];
const LANGUAGES = ["en", "ur", "ur-Latn"];

const EMPTY: ResourceInput = {
  title: "",
  url: "",
  type: "course",
  provider: "",
  description: "",
  is_free: true,
  difficulty: "beginner",
  career_slugs: [],
  language: "en",
  is_active: true,
};

type Filter = "all" | "active" | "off";

export default function AdminResourcesPage() {
  const t = useTranslations("admin.resources");
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [page, setPage] = useState(0);
  const [editing, setEditing] = useState<{ id: string | null; data: ResourceInput } | null>(null);

  const query = useQuery({
    queryKey: ["admin", "resources", search, filter, page],
    queryFn: () =>
      listAdminResources({
        search: search || undefined,
        active: filter === "all" ? undefined : filter === "active",
        limit: PAGE,
        offset: page * PAGE,
      }),
    placeholderData: keepPreviousData,
  });

  const save = useMutation({
    mutationFn: ({ id, data }: { id: string | null; data: ResourceInput }) =>
      id ? updateResource(id, data) : createResource(data),
    onSuccess: () => {
      toast.success(t("saved"));
      setEditing(null);
      queryClient.invalidateQueries({ queryKey: ["admin", "resources"] });
    },
    onError: (error) => toast.error(apiErrorMessage(error, t("failed"))),
  });

  const open = (row: AdminResource | null) =>
    setEditing(
      row
        ? { id: row.id, data: { ...row, provider: row.provider ?? "", description: row.description ?? "" } }
        : { id: null, data: EMPTY }
    );

  const total = query.data?.total ?? 0;
  const last = Math.max(0, Math.ceil(total / PAGE) - 1);

  function submit(event: React.FormEvent) {
    event.preventDefault();

    if (!editing) return;

    const d = editing.data;

    save.mutate({
      id: editing.id,
      data: {
        ...d,
        provider: d.provider?.trim() || null,
        description: d.description?.trim() || null,
        career_slugs: d.career_slugs.filter(Boolean),
      },
    });
  }

  const patch = (change: Partial<ResourceInput>) =>
    setEditing((prev) => (prev ? { ...prev, data: { ...prev.data, ...change } } : prev));

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <SearchField
          value={search}
          onChange={(v) => {
            setSearch(v);
            setPage(0);
          }}
          placeholder={t("search")}
          className="min-w-64 flex-1"
        />
        <FilterChips
          label={t("filter")}
          size="sm"
          value={filter}
          onChange={(v) => {
            setFilter(v);
            setPage(0);
          }}
          options={[
            { value: "all", label: t("all") },
            { value: "active", label: t("active") },
            { value: "off", label: t("off") },
          ]}
        />
        <Button className="gap-2" onClick={() => open(null)}>
          <Plus size={16} /> {t("new")}
        </Button>
      </div>

      {query.isError ? (
        <EmptyState icon={BookOpen} title={t("loadFailed")} />
      ) : (
        <Card className="overflow-x-auto p-0">
          <table className="w-full min-w-[720px] text-sm">
            <thead>
              <tr className="border-b text-xs text-muted-foreground">
                <th className="p-3 text-start font-medium">{t("title")}</th>
                <th className="p-3 text-start font-medium">{t("type")}</th>
                <th className="p-3 text-start font-medium">{t("level")}</th>
                <th className="p-3 text-start font-medium">{t("careers")}</th>
                <th className="p-3 text-start font-medium">{t("status")}</th>
                <th className="p-3" />
              </tr>
            </thead>
            <tbody>
              {(query.data?.items ?? []).map((r) => (
                <tr key={r.id} className="border-b last:border-0">
                  <td className="max-w-xs p-3">
                    <a href={r.url} target="_blank" rel="noopener noreferrer" className="line-clamp-1 font-medium hover:underline">
                      {r.title}
                    </a>
                    <span className="text-xs text-muted-foreground">{r.provider}</span>
                  </td>
                  <td className="p-3 text-muted-foreground">{r.type}</td>
                  <td className="p-3 text-muted-foreground">{r.difficulty ?? "-"}</td>
                  <td className="p-3 text-muted-foreground">{r.career_slugs.length}</td>
                  <td className="p-3">
                    <Pill tone={r.is_active ? "gold" : "soft"}>{r.is_active ? t("active") : t("off")}</Pill>
                  </td>
                  <td className="p-3 text-end">
                    <Button variant="ghost" size="icon" aria-label={t("edit", { title: r.title })} onClick={() => open(r)}>
                      <Pencil size={15} />
                    </Button>
                  </td>
                </tr>
              ))}
              {query.data && query.data.items.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-muted-foreground">{t("none")}</td>
                </tr>
              )}
            </tbody>
          </table>
        </Card>
      )}

      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>{t("total", { count: total })}</span>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage(page - 1)}>{t("previous")}</Button>
          <Button variant="outline" size="sm" disabled={page >= last} onClick={() => setPage(page + 1)}>{t("next")}</Button>
        </div>
      </div>

      <Dialog open={editing !== null} onOpenChange={(o) => !o && setEditing(null)}>
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>{editing?.id ? t("editTitle") : t("newTitle")}</DialogTitle>
            <DialogDescription>{t("dialogText")}</DialogDescription>
          </DialogHeader>

          {editing && (
            <form onSubmit={submit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="r-title">{t("title")}</Label>
                <Input id="r-title" required value={editing.data.title} onChange={(e) => patch({ title: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="r-url">{t("link")}</Label>
                <Input id="r-url" required placeholder="https://" value={editing.data.url} onChange={(e) => patch({ url: e.target.value })} />
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="space-y-1.5">
                  <Label htmlFor="r-type">{t("type")}</Label>
                  <NativeSelect id="r-type" value={editing.data.type} onChange={(e) => patch({ type: e.target.value })}>
                    {TYPES.map((v) => <option key={v} value={v}>{v}</option>)}
                  </NativeSelect>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="r-level">{t("level")}</Label>
                  <NativeSelect id="r-level" value={editing.data.difficulty ?? ""} onChange={(e) => patch({ difficulty: e.target.value || null })}>
                    {LEVELS.map((v) => <option key={v} value={v}>{v}</option>)}
                  </NativeSelect>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="r-lang">{t("language")}</Label>
                  <NativeSelect id="r-lang" value={editing.data.language} onChange={(e) => patch({ language: e.target.value })}>
                    {LANGUAGES.map((v) => <option key={v} value={v}>{v}</option>)}
                  </NativeSelect>
                </div>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="r-provider">{t("provider")}</Label>
                <Input id="r-provider" value={editing.data.provider ?? ""} onChange={(e) => patch({ provider: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="r-desc">{t("description")}</Label>
                <Textarea id="r-desc" className="min-h-20" value={editing.data.description ?? ""} onChange={(e) => patch({ description: e.target.value })} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="r-careers">{t("careersField")}</Label>
                <Input
                  id="r-careers"
                  placeholder="backend-engineer, data-analyst"
                  value={editing.data.career_slugs.join(", ")}
                  onChange={(e) => patch({ career_slugs: e.target.value.split(",").map((s) => s.trim()) })}
                />
                <p className="text-xs text-muted-foreground">{t("careersHint")}</p>
              </div>
              <div className="flex flex-wrap gap-6">
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" className="size-4 accent-gold" checked={editing.data.is_free} onChange={(e) => patch({ is_free: e.target.checked })} />
                  {t("free")}
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" className="size-4 accent-gold" checked={editing.data.is_active} onChange={(e) => patch({ is_active: e.target.checked })} />
                  {t("showToLearners")}
                </label>
              </div>
              <div className="flex gap-3">
                <LoadingButton type="submit" loading={save.isPending}>{t("save")}</LoadingButton>
                <Button type="button" variant="outline" onClick={() => setEditing(null)}>{t("cancel")}</Button>
              </div>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
