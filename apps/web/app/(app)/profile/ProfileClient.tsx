"use client";

import { useState } from "react";
import PageHeader from "@/components/shared/PageHeader";
import { useRouter } from "next/navigation";
import {
  Briefcase,
  CalendarDays,
  Clock,
  Flame,
  Gauge,
  Globe,
  GraduationCap,
  MapPin,
  Pencil,
  Target,
  UserCog,
  Zap,
} from "lucide-react";
import { useLocale, useTranslations } from "next-intl";

import { setLocaleCookie } from "@/app/actions/locale";
import { toast } from "sonner";

import { patchProfile } from "@/lib/api/profile";
import {
  apiErrorMessage,
  CAREER_STAGES,
  DEVICES,
  EDUCATION,
  GOAL_TYPES,
  labelFor,
  LANGUAGES,
  LEARNING_STYLES,
  PACES,
  SKILL_LEVELS,
  STUDY_HOURS,
} from "@/lib/profile-options";
import { useCareerOptions } from "@/lib/careers";
import { formatDate } from "@/lib/format";
import { useTimezones } from "@/lib/use-timezones";
import { authService } from "@/services/auth/auth";
import { useAuthStore } from "@/store/auth";
import { Gamification, ProfileChanges, ProfileData } from "@/types/api";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import LoadingButton from "@/components/shared/LoadingButton";
import NativeSelect from "@/components/shared/NativeSelect";

interface Props {
  profile: ProfileData | null;
  gamification: Gamification | null;
  account: { email: string; fallbackName: string; avatarUrl: string | null };
}

interface FormState {
  full_name: string;
  language: string;
  country: string;
  timezone: string;
  career_slug: string;
  skill_level: string;
  learning_style: string;
  career_stage: string;
  daily_hours: string;
  target_duration: string;
  learning_goal: string;
  age: string;
  education: string;
  device: string;
  goal_type: string;
  preferred_study_hours: string;
  learning_pace: string;
  weekend_study: string; // "", "yes" or "no"
}

function toForm(p: ProfileData): FormState {
  return {
    full_name: p.full_name ?? "",
    language: p.language ?? "en",
    country: p.country ?? "",
    timezone: p.timezone ?? "",
    career_slug: p.career_slug ?? "",
    skill_level: p.skill_level ?? "beginner",
    learning_style: p.learning_style ?? "reading",
    career_stage: p.career_stage ?? "",
    daily_hours: String(p.daily_hours ?? 2),
    target_duration: String(p.target_duration ?? 6),
    learning_goal: p.learning_goal ?? "",
    age: p.age == null ? "" : String(p.age),
    education: p.education ?? "",
    device: p.device ?? "",
    goal_type: p.goal_type ?? "",
    preferred_study_hours: p.preferred_study_hours ?? "",
    learning_pace: p.learning_pace ?? "",
    weekend_study:
      p.weekend_study == null ? "" : p.weekend_study ? "yes" : "no",
  };
}

/** Only what changed, so an edit never overwrites fields it didn't touch. */
function diff(before: FormState, after: FormState): ProfileChanges {
  const out: Record<string, unknown> = {};

  (Object.keys(after) as (keyof FormState)[]).forEach((key) => {
    if (after[key] === before[key]) return;

    const value = after[key];

    if (key === "daily_hours" || key === "target_duration") {
      out[key] = Number(value);
    } else if (key === "full_name") {
      out[key] = value.trim();
    } else if (key === "age") {
      out[key] = value.trim() === "" ? null : Number(value);
    } else if (key === "weekend_study") {
      out[key] = value === "" ? null : value === "yes";
    } else if (
      key === "education" ||
      key === "device" ||
      key === "goal_type" ||
      key === "preferred_study_hours" ||
      key === "learning_pace"
    ) {
      out[key] = value === "" ? null : value;
    } else if (
      key === "country" ||
      key === "timezone" ||
      key === "career_stage" ||
      key === "learning_goal"
    ) {
      out[key] = value.trim() === "" ? null : value.trim();
    } else {
      out[key] = value;
    }
  });

  return out as ProfileChanges;
}

function validate(form: FormState): "name" | "hours" | "months" | "age" | null {
  if (!form.full_name.trim()) return "name";

  const hours = Number(form.daily_hours);
  if (!Number.isInteger(hours) || hours < 1 || hours > 12) {
    return "hours";
  }

  const months = Number(form.target_duration);
  if (!Number.isInteger(months) || months < 1 || months > 36) {
    return "months";
  }

  if (form.age.trim() !== "") {
    const age = Number(form.age);
    if (!Number.isInteger(age) || age < 10 || age > 100) {
      return "age";
    }
  }

  return null;
}

function Detail({
  icon: Icon,
  label,
  value,
  wide,
}: {
  icon: typeof Globe;
  label: string;
  value: string;
  wide?: boolean;
}) {
  return (
    <Card
      className={`flex-row items-start gap-4 p-5 ${wide ? "sm:col-span-2" : ""}`}
    >
      <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-brand-gold/15 text-brand-gold-deep dark:text-brand-gold">
        <Icon size={18} />
      </span>
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="break-words font-medium">{value}</p>
      </div>
    </Card>
  );
}

function Field({
  id,
  label,
  hint,
  children,
}: {
  id: string;
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="min-w-0 space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

function useChoiceLabel() {
  const o = useTranslations("options");
  const t = useTranslations("profile");

  return (group: string, value: string | null) =>
    value ? o(`${group}.${value}`) : t("notSet");
}

export default function ProfileClient({
  profile,
  gamification,
  account,
  initialEditing = false,
}: Props & { initialEditing?: boolean }) {
  const t = useTranslations("profile");
  const choiceLabel = useChoiceLabel();
  const { options: CAREERS } = useCareerOptions();
  const o = useTranslations("options");
  const router = useRouter();
  const locale = useLocale();
  const setUser = useAuthStore((state) => state.setUser);

  const [current, setCurrent] = useState(profile);
  const [editing, setEditing] = useState(initialEditing && !!profile);
  const [form, setForm] = useState<FormState | null>(
    profile ? toForm(profile) : null
  );
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const { options: timezones } = useTimezones(current?.timezone);

  const name = current?.full_name || account.fallbackName;
  const initials = name
    .split(" ")
    .map((n) => n[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  function set<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  function startEditing() {
    if (!current) return;
    setForm(toForm(current));
    setError(null);
    setEditing(true);
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!current || !form) return;

    const problem = validate(form);
    if (problem) {
      setError(t(`errors.${problem}`));
      return;
    }

    const changes = diff(toForm(current), form);

    if (Object.keys(changes).length === 0) {
      setEditing(false);
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const updated = await patchProfile(changes);
      setCurrent(updated);
      setForm(toForm(updated));

      // Keep the login's display name in step so the greeting updates too.
      if (changes.full_name) {
        const { data } = await authService.updateFullName(updated.full_name);
        if (data.user) setUser(data.user);
      }

      setEditing(false);
      toast.success(t("updated"));

      // A new language applies to the app right away.
      if (changes.language) await setLocaleCookie(changes.language);

      router.refresh();
    } catch (err) {
      setError(apiErrorMessage(err, t("saveFailed")));
    } finally {
      setSaving(false);
    }
  }

  const stats = gamification
    ? [
        { icon: Zap, label: t("level"), value: t("levelValue", { level: gamification.level }) },
        { icon: Flame, label: t("streak"), value: String(gamification.streak_days) },
        { icon: Target, label: t("xp"), value: String(gamification.xp) },
        {
          icon: CalendarDays,
          label: t("since"),
          value: current?.created_at
            ? formatDate(current.created_at, { month: "short", year: "numeric" }, locale)
            : "—",
        },
      ]
    : [];

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title={t("title")} subtitle={t("subtitle")} />

      <Card className="mt-6 flex-col gap-4 p-6 sm:flex-row sm:items-center sm:gap-5">
        <Avatar size="lg" className="size-16 shrink-0">
          <AvatarImage src={account.avatarUrl ?? undefined} />
          <AvatarFallback className="bg-brand-violet text-lg text-white">
            {initials}
          </AvatarFallback>
        </Avatar>
        <div className="min-w-0 flex-1">
          <p className="font-heading break-words text-xl font-bold">{name}</p>
          <p className="break-all text-sm text-muted-foreground">
            {account.email}
          </p>
        </div>
        {current && !editing && (
          <Button variant="outline" size="sm" className="gap-2" onClick={startEditing}>
            <Pencil size={14} /> {t("edit")}
          </Button>
        )}
      </Card>

      {stats.length > 0 && (
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {stats.map(({ icon: Icon, label, value }) => (
            <Card key={label} className="items-start gap-1 p-4">
              <Icon size={16} className="text-brand-violet" />
              <p className="text-lg font-bold leading-tight">{value}</p>
              <p className="text-xs text-muted-foreground">{label}</p>
            </Card>
          ))}
        </div>
      )}

      <h2 className="font-heading mt-8 text-lg font-semibold">
        {editing ? t("editTitle") : t("prefsTitle")}
      </h2>

      {!current || !form ? (
        <Card className="mt-3 items-center p-8 text-center">
          <p className="text-sm text-muted-foreground">
            {t("loadFailed")}
          </p>
        </Card>
      ) : editing ? (
        <form onSubmit={save} className="mt-3">
          <Card className="gap-5 p-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field id="full_name" label={t("fields.full_name")}>
                <Input
                  id="full_name"
                  value={form.full_name}
                  maxLength={100}
                  onChange={(e) => set("full_name", e.target.value)}
                />
              </Field>

              <Field id="language" label={t("fields.language")}>
                <NativeSelect
                  id="language"
                  value={form.language}
                  onChange={(e) => set("language", e.target.value)}
                >
                  {LANGUAGES.map((l) => (
                    <option key={l.value} value={l.value}>
                      {l.label}
                    </option>
                  ))}
                </NativeSelect>
              </Field>

              <Field id="country" label={t("fields.country")}>
                <Input
                  id="country"
                  value={form.country}
                  maxLength={60}
                  placeholder={t("fields.countryExample")}
                  onChange={(e) => set("country", e.target.value)}
                />
              </Field>

              <Field id="timezone" label={t("fields.timezone")}>
                <NativeSelect
                  id="timezone"
                  value={form.timezone}
                  onChange={(e) => set("timezone", e.target.value)}
                >
                  <option value="">{t("notSet")}</option>
                  {timezones.map((z) => (
                    <option key={z} value={z}>
                      {z}
                    </option>
                  ))}
                </NativeSelect>
              </Field>

              <Field id="career_slug" label={t("fields.career_slug")}>
                <NativeSelect
                  id="career_slug"
                  value={form.career_slug}
                  onChange={(e) => set("career_slug", e.target.value)}
                >
                  {!CAREERS.some((c) => c.value === form.career_slug) && (
                    <option value={form.career_slug}>{t("fields.chooseCareer")}</option>
                  )}
                  {CAREERS.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </NativeSelect>
              </Field>

              <Field id="career_stage" label={t("fields.career_stage")}>
                <NativeSelect
                  id="career_stage"
                  value={form.career_stage}
                  onChange={(e) => set("career_stage", e.target.value)}
                >
                  <option value="">{t("notSet")}</option>
                  {CAREER_STAGES.map((s) => (
                    <option key={s.value} value={s.value}>
                      {o(`career_stage.${s.value}`)}
                    </option>
                  ))}
                </NativeSelect>
              </Field>

              <Field id="skill_level" label={t("fields.skill_level")}>
                <NativeSelect
                  id="skill_level"
                  value={form.skill_level}
                  onChange={(e) => set("skill_level", e.target.value)}
                >
                  {SKILL_LEVELS.map((s) => (
                    <option key={s.value} value={s.value}>
                      {o(`skill_level.${s.value}`)}
                    </option>
                  ))}
                </NativeSelect>
              </Field>

              <Field id="learning_style" label={t("fields.learning_style")}>
                <NativeSelect
                  id="learning_style"
                  value={form.learning_style}
                  onChange={(e) => set("learning_style", e.target.value)}
                >
                  {LEARNING_STYLES.map((s) => (
                    <option key={s.value} value={s.value}>
                      {o(`learning_style.${s.value}`)}
                    </option>
                  ))}
                </NativeSelect>
              </Field>

              <Field id="daily_hours" label={t("fields.daily_hours")}>
                <Input
                  id="daily_hours"
                  type="number"
                  inputMode="numeric"
                  min={1}
                  max={12}
                  value={form.daily_hours}
                  onChange={(e) => set("daily_hours", e.target.value)}
                />
              </Field>

              <Field id="target_duration" label={t("fields.target_duration")}>
                <Input
                  id="target_duration"
                  type="number"
                  inputMode="numeric"
                  min={1}
                  max={36}
                  value={form.target_duration}
                  onChange={(e) => set("target_duration", e.target.value)}
                />
              </Field>

              <Field id="age" label={t("fields.age")}>
                <Input
                  id="age"
                  type="number"
                  inputMode="numeric"
                  min={10}
                  max={100}
                  value={form.age}
                  onChange={(e) => set("age", e.target.value)}
                />
              </Field>

              <Field id="education" label={t("fields.education")}>
                <NativeSelect
                  id="education"
                  value={form.education}
                  onChange={(e) => set("education", e.target.value)}
                >
                  <option value="">{t("notSet")}</option>
                  {EDUCATION.map((v) => (
                    <option key={v} value={v}>
                      {o(`education.${v}`)}
                    </option>
                  ))}
                </NativeSelect>
              </Field>

              <Field id="device" label={t("fields.device")}>
                <NativeSelect
                  id="device"
                  value={form.device}
                  onChange={(e) => set("device", e.target.value)}
                >
                  <option value="">{t("notSet")}</option>
                  {DEVICES.map((v) => (
                    <option key={v} value={v}>
                      {o(`device.${v}`)}
                    </option>
                  ))}
                </NativeSelect>
              </Field>

              <Field id="goal_type" label={t("fields.goal_type")}>
                <NativeSelect
                  id="goal_type"
                  value={form.goal_type}
                  onChange={(e) => set("goal_type", e.target.value)}
                >
                  <option value="">{t("notSet")}</option>
                  {GOAL_TYPES.map((v) => (
                    <option key={v} value={v}>
                      {o(`goal_type.${v}`)}
                    </option>
                  ))}
                </NativeSelect>
              </Field>

              <Field id="preferred_study_hours" label={t("fields.preferred_study_hours")}>
                <NativeSelect
                  id="preferred_study_hours"
                  value={form.preferred_study_hours}
                  onChange={(e) => set("preferred_study_hours", e.target.value)}
                >
                  <option value="">{t("notSet")}</option>
                  {STUDY_HOURS.map((v) => (
                    <option key={v} value={v}>
                      {o(`study_hours.${v}`)}
                    </option>
                  ))}
                </NativeSelect>
              </Field>

              <Field id="learning_pace" label={t("fields.learning_pace")}>
                <NativeSelect
                  id="learning_pace"
                  value={form.learning_pace}
                  onChange={(e) => set("learning_pace", e.target.value)}
                >
                  <option value="">{t("notSet")}</option>
                  {PACES.map((v) => (
                    <option key={v} value={v}>
                      {o(`pace.${v}`)}
                    </option>
                  ))}
                </NativeSelect>
              </Field>

              <Field id="weekend_study" label={t("fields.weekend_study")}>
                <NativeSelect
                  id="weekend_study"
                  value={form.weekend_study}
                  onChange={(e) => set("weekend_study", e.target.value)}
                >
                  <option value="">{t("notSet")}</option>
                  <option value="yes">{t("weekendYes")}</option>
                  <option value="no">{t("weekendNo")}</option>
                </NativeSelect>
              </Field>
            </div>

            <Field id="learning_goal" label={t("fields.learning_goal")}>
              <Textarea
                id="learning_goal"
                value={form.learning_goal}
                maxLength={255}
                placeholder={t("fields.goalExample")}
                className="min-h-20"
                onChange={(e) => set("learning_goal", e.target.value)}
              />
            </Field>

            <p className="text-xs text-muted-foreground">
              {t("appliesNew")}
            </p>

            {error && (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            )}

            <div className="flex flex-wrap gap-3">
              <LoadingButton type="submit" loading={saving}>
                {t("save")}
              </LoadingButton>
              <Button
                type="button"
                variant="outline"
                disabled={saving}
                onClick={() => {
                  setEditing(false);
                  setError(null);
                }}
              >
                {t("cancel")}
              </Button>
            </div>
          </Card>
        </form>
      ) : (
        <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Detail icon={Briefcase} label={t("fields.career_slug")} value={labelFor(CAREERS, current.career_slug)} />
          <Detail icon={UserCog} label={t("fields.career_stage")} value={choiceLabel("career_stage", current.career_stage)} />
          <Detail icon={Gauge} label={t("fields.skill_level")} value={choiceLabel("skill_level", current.skill_level)} />
          <Detail icon={GraduationCap} label={t("fields.learning_style")} value={choiceLabel("learning_style", current.learning_style)} />
          <Detail icon={Clock} label={t("fields.dailyStudy")} value={t("perDay", { count: current.daily_hours })} />
          <Detail icon={Target} label={t("fields.target")} value={t("months", { count: current.target_duration })} />
          <Detail icon={CalendarDays} label={t("fields.age")} value={current.age ? String(current.age) : t("notSet")} />
          <Detail icon={GraduationCap} label={t("fields.education")} value={choiceLabel("education", current.education)} />
          <Detail icon={Gauge} label={t("fields.device")} value={choiceLabel("device", current.device)} />
          <Detail icon={Target} label={t("fields.goal_type")} value={choiceLabel("goal_type", current.goal_type)} />
          <Detail icon={Clock} label={t("fields.preferred_study_hours")} value={choiceLabel("study_hours", current.preferred_study_hours)} />
          <Detail icon={Zap} label={t("fields.learning_pace")} value={choiceLabel("pace", current.learning_pace)} />
          <Detail icon={CalendarDays} label={t("fields.weekend_study")} value={current.weekend_study == null ? t("notSet") : current.weekend_study ? t("weekendYes") : t("weekendNo")} />
          <Detail icon={Globe} label={t("fields.language")} value={labelFor(LANGUAGES, current.language)} />
          <Detail icon={MapPin} label={t("fields.location")} value={[current.country, current.timezone].filter(Boolean).join(" · ") || t("notSet")} />
          <Detail icon={Target} label={t("fields.learning_goal")} value={current.learning_goal || t("notSet")} wide />
        </div>
      )}
    </div>
  );
}
