"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import {
  AdminCareer,
  CareerInput,
  CareerResourceInput,
  createCareer,
  updateCareer,
} from "@/lib/api/admin";
import { apiErrorMessage } from "@/lib/profile-options";

import LoadingButton from "@/components/shared/LoadingButton";
import NativeSelect from "@/components/shared/NativeSelect";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

const LEVELS = ["beginner", "intermediate", "advanced"];
const DEMANDS = ["low", "medium", "high", "very_high"];
const TYPES = ["course", "video", "docs", "book", "practice"];

const EMPTY: CareerInput & { slug: string } = {
  slug: "",
  name: "",
  description: "",
  category: "",
  icon: "Briefcase",
  color: "#7C3AED",
  difficulty: "beginner",
  estimated_months: 6,
  salary_min_pkr: null,
  salary_max_pkr: null,
  market_demand: "medium",
  is_active: true,
  skills: [],
  resources: [],
};

const blank = (value: string) => (value.trim() === "" ? null : value);
const number = (value: string) => (value.trim() === "" ? null : Number(value));

/** One form for adding and editing a career. A career's address (slug) is fixed
 * once saved: roadmaps and profiles point at it. */
export default function CareerForm({ career }: { career?: AdminCareer }) {
  const t = useTranslations("admin.careers.form");
  const router = useRouter();
  const queryClient = useQueryClient();
  const editing = !!career;

  const [form, setForm] = useState<CareerInput & { slug: string }>(career ?? EMPTY);
  const [saving, setSaving] = useState(false);

  const set = <K extends keyof typeof form>(key: K, value: (typeof form)[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const setResource = (index: number, patch: Partial<CareerResourceInput>) =>
    set("resources", form.resources.map((r, i) => (i === index ? { ...r, ...patch } : r)));

  async function save(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);

    const { slug, ...fields } = form;
    const body: CareerInput = {
      ...fields,
      category: blank(fields.category ?? ""),
      icon: blank(fields.icon ?? ""),
      skills: fields.skills.filter((s) => s.name.trim()),
      resources: fields.resources.filter((r) => r.title.trim() && r.url.trim()),
    };

    try {
      if (editing) {
        await updateCareer(career.id, body);
        toast.success(t("saved"));
      } else {
        await createCareer({ ...body, slug });
        toast.success(t("created"));
      }

      await queryClient.invalidateQueries({ queryKey: ["admin", "careers"] });
      router.push("/admin/careers");
      router.refresh();
    } catch (error) {
      toast.error(apiErrorMessage(error, t("failed")));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={save} className="space-y-6">
      <Card className="gap-5 p-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="name">{t("name")}</Label>
            <Input id="name" required value={form.name} onChange={(e) => set("name", e.target.value)} />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="slug">{t("slug")}</Label>
            <Input
              id="slug"
              required
              disabled={editing}
              value={form.slug}
              placeholder="data-analyst"
              onChange={(e) => set("slug", e.target.value.toLowerCase())}
            />
            <p className="text-xs text-muted-foreground">{editing ? t("slugFixed") : t("slugHint")}</p>
          </div>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="description">{t("description")}</Label>
          <Textarea
            id="description"
            required
            minLength={10}
            className="min-h-24"
            value={form.description}
            onChange={(e) => set("description", e.target.value)}
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="space-y-1.5">
            <Label htmlFor="category">{t("category")}</Label>
            <Input id="category" value={form.category ?? ""} onChange={(e) => set("category", e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="icon">{t("icon")}</Label>
            <Input id="icon" value={form.icon ?? ""} onChange={(e) => set("icon", e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="color">{t("color")}</Label>
            <Input id="color" value={form.color ?? ""} placeholder="#7C3AED" onChange={(e) => set("color", blank(e.target.value))} />
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="space-y-1.5">
            <Label htmlFor="difficulty">{t("difficulty")}</Label>
            <NativeSelect id="difficulty" value={form.difficulty ?? ""} onChange={(e) => set("difficulty", blank(e.target.value))}>
              {LEVELS.map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </NativeSelect>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="demand">{t("demand")}</Label>
            <NativeSelect id="demand" value={form.market_demand ?? ""} onChange={(e) => set("market_demand", blank(e.target.value))}>
              {DEMANDS.map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </NativeSelect>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="months">{t("months")}</Label>
            <Input
              id="months"
              type="number"
              min={1}
              max={60}
              value={form.estimated_months ?? ""}
              onChange={(e) => set("estimated_months", number(e.target.value))}
            />
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="salary-min">{t("salaryMin")}</Label>
            <Input id="salary-min" type="number" min={0} value={form.salary_min_pkr ?? ""} onChange={(e) => set("salary_min_pkr", number(e.target.value))} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="salary-max">{t("salaryMax")}</Label>
            <Input id="salary-max" type="number" min={0} value={form.salary_max_pkr ?? ""} onChange={(e) => set("salary_max_pkr", number(e.target.value))} />
          </div>
        </div>

        <label className="flex cursor-pointer items-center gap-3 text-sm">
          <input
            type="checkbox"
            className="size-4 accent-gold"
            checked={form.is_active}
            onChange={(e) => set("is_active", e.target.checked)}
          />
          <span>
            <span className="font-medium">{t("active")}</span>
            <span className="block text-xs text-muted-foreground">{t("activeHint")}</span>
          </span>
        </label>
      </Card>

      <Card className="gap-3 p-6">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-lg font-semibold">{t("skills")}</h2>
          <Button type="button" variant="outline" size="sm" className="gap-2" onClick={() => set("skills", [...form.skills, { name: "" }])}>
            <Plus size={14} /> {t("addSkill")}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">{t("skillsHint")}</p>
        {form.skills.map((skill, i) => (
          <div key={i} className="flex gap-2">
            <Input
              aria-label={t("skillN", { number: i + 1 })}
              value={skill.name}
              onChange={(e) => set("skills", form.skills.map((s, j) => (j === i ? { name: e.target.value } : s)))}
            />
            <Button type="button" variant="ghost" size="icon" aria-label={t("remove")} onClick={() => set("skills", form.skills.filter((_, j) => j !== i))}>
              <Trash2 size={15} />
            </Button>
          </div>
        ))}
      </Card>

      <Card className="gap-4 p-6">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-lg font-semibold">{t("resources")}</h2>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="gap-2"
            onClick={() =>
              set("resources", [
                ...form.resources,
                { title: "", type: "course", provider: "", url: "", is_free: true, difficulty: "beginner" },
              ])
            }
          >
            <Plus size={14} /> {t("addResource")}
          </Button>
        </div>
        {form.resources.map((r, i) => (
          <div key={i} className="grid gap-2 rounded-2xl border p-3 sm:grid-cols-[1fr_1fr_auto]">
            <Input aria-label={t("resourceTitle")} placeholder={t("resourceTitle")} value={r.title} onChange={(e) => setResource(i, { title: e.target.value })} />
            <Input aria-label={t("resourceUrl")} placeholder="https://" value={r.url} onChange={(e) => setResource(i, { url: e.target.value })} />
            <Button type="button" variant="ghost" size="icon" aria-label={t("remove")} onClick={() => set("resources", form.resources.filter((_, j) => j !== i))}>
              <Trash2 size={15} />
            </Button>
            <Input aria-label={t("provider")} placeholder={t("provider")} value={r.provider ?? ""} onChange={(e) => setResource(i, { provider: blank(e.target.value) })} />
            <div className="flex gap-2">
              <NativeSelect aria-label={t("type")} value={r.type} onChange={(e) => setResource(i, { type: e.target.value })}>
                {TYPES.map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </NativeSelect>
              <NativeSelect aria-label={t("difficulty")} value={r.difficulty ?? ""} onChange={(e) => setResource(i, { difficulty: blank(e.target.value) })}>
                {LEVELS.map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </NativeSelect>
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" className="size-4 accent-gold" checked={r.is_free} onChange={(e) => setResource(i, { is_free: e.target.checked })} />
              {t("free")}
            </label>
          </div>
        ))}
      </Card>

      <div className="flex gap-3">
        <LoadingButton type="submit" loading={saving}>
          {editing ? t("save") : t("create")}
        </LoadingButton>
        <Button type="button" variant="outline" onClick={() => router.push("/admin/careers")}>
          {t("cancel")}
        </Button>
      </div>
    </form>
  );
}
