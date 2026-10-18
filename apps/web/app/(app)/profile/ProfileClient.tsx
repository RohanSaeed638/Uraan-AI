"use client";

import { useState } from "react";
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
import { toast } from "sonner";

import { patchProfile } from "@/lib/api/profile";
import {
  apiErrorMessage,
  CAREER_STAGES,
  CAREERS,
  labelFor,
  LANGUAGES,
  LEARNING_STYLES,
  SKILL_LEVELS,
} from "@/lib/profile-options";
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

function validate(form: FormState): string | null {
  if (!form.full_name.trim()) return "Please enter your name.";

  const hours = Number(form.daily_hours);
  if (!Number.isInteger(hours) || hours < 1 || hours > 12) {
    return "Daily study time must be a whole number from 1 to 12 hours.";
  }

  const months = Number(form.target_duration);
  if (!Number.isInteger(months) || months < 1 || months > 36) {
    return "Target duration must be a whole number from 1 to 36 months.";
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
      <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-brand-violet/10 text-brand-violet">
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

export default function ProfileClient({
  profile,
  gamification,
  account,
  initialEditing = false,
}: Props & { initialEditing?: boolean }) {
  const router = useRouter();
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
      setError(problem);
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
      toast.success("Profile updated.");
      router.refresh();
    } catch (err) {
      setError(apiErrorMessage(err, "Couldn't save your profile. Try again."));
    } finally {
      setSaving(false);
    }
  }

  const stats = gamification
    ? [
        { icon: Zap, label: "Level", value: `Level ${gamification.level}` },
        { icon: Flame, label: "Day streak", value: String(gamification.streak_days) },
        { icon: Target, label: "Total XP", value: String(gamification.xp) },
        {
          icon: CalendarDays,
          label: "Member since",
          value: current?.created_at
            ? formatDate(current.created_at, { month: "short", year: "numeric" })
            : "—",
        },
      ]
    : [];

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="font-heading text-3xl font-bold">Profile</h1>
      <p className="mt-1 text-muted-foreground">
        Your personal details and learning preferences.
      </p>

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
            <Pencil size={14} /> Edit profile
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
        {editing ? "Edit your profile" : "Learning preferences"}
      </h2>

      {!current || !form ? (
        <Card className="mt-3 items-center p-8 text-center">
          <p className="text-sm text-muted-foreground">
            Your profile couldn&apos;t be loaded right now. Refresh the page to
            try again.
          </p>
        </Card>
      ) : editing ? (
        <form onSubmit={save} className="mt-3">
          <Card className="gap-5 p-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field id="full_name" label="Full name">
                <Input
                  id="full_name"
                  value={form.full_name}
                  maxLength={100}
                  onChange={(e) => set("full_name", e.target.value)}
                />
              </Field>

              <Field id="language" label="Language">
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

              <Field id="country" label="Country">
                <Input
                  id="country"
                  value={form.country}
                  maxLength={60}
                  placeholder="e.g. Pakistan"
                  onChange={(e) => set("country", e.target.value)}
                />
              </Field>

              <Field id="timezone" label="Timezone">
                <NativeSelect
                  id="timezone"
                  value={form.timezone}
                  onChange={(e) => set("timezone", e.target.value)}
                >
                  <option value="">Not set</option>
                  {timezones.map((z) => (
                    <option key={z} value={z}>
                      {z}
                    </option>
                  ))}
                </NativeSelect>
              </Field>

              <Field id="career_slug" label="Career path">
                <NativeSelect
                  id="career_slug"
                  value={form.career_slug}
                  onChange={(e) => set("career_slug", e.target.value)}
                >
                  {!CAREERS.some((c) => c.value === form.career_slug) && (
                    <option value={form.career_slug}>Choose a career…</option>
                  )}
                  {CAREERS.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </NativeSelect>
              </Field>

              <Field id="career_stage" label="Where you are now">
                <NativeSelect
                  id="career_stage"
                  value={form.career_stage}
                  onChange={(e) => set("career_stage", e.target.value)}
                >
                  <option value="">Not set</option>
                  {CAREER_STAGES.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </NativeSelect>
              </Field>

              <Field id="skill_level" label="Skill level">
                <NativeSelect
                  id="skill_level"
                  value={form.skill_level}
                  onChange={(e) => set("skill_level", e.target.value)}
                >
                  {SKILL_LEVELS.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </NativeSelect>
              </Field>

              <Field id="learning_style" label="Learning style">
                <NativeSelect
                  id="learning_style"
                  value={form.learning_style}
                  onChange={(e) => set("learning_style", e.target.value)}
                >
                  {LEARNING_STYLES.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </NativeSelect>
              </Field>

              <Field id="daily_hours" label="Daily study time (hours)">
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

              <Field id="target_duration" label="Target duration (months)">
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
            </div>

            <Field id="learning_goal" label="Your goal">
              <Textarea
                id="learning_goal"
                value={form.learning_goal}
                maxLength={255}
                placeholder="e.g. Get a junior backend job in 6 months"
                className="min-h-20"
                onChange={(e) => set("learning_goal", e.target.value)}
              />
            </Field>

            <p className="text-xs text-muted-foreground">
              Changes apply to new roadmaps and lessons. Roadmaps you already
              created keep the style they were made with.
            </p>

            {error && (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            )}

            <div className="flex flex-wrap gap-3">
              <LoadingButton type="submit" loading={saving}>
                Save changes
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
                Cancel
              </Button>
            </div>
          </Card>
        </form>
      ) : (
        <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Detail icon={Briefcase} label="Career path" value={labelFor(CAREERS, current.career_slug)} />
          <Detail icon={UserCog} label="Where you are now" value={labelFor(CAREER_STAGES, current.career_stage)} />
          <Detail icon={Gauge} label="Skill level" value={labelFor(SKILL_LEVELS, current.skill_level)} />
          <Detail icon={GraduationCap} label="Learning style" value={labelFor(LEARNING_STYLES, current.learning_style)} />
          <Detail icon={Clock} label="Daily study time" value={`${current.daily_hours}h per day`} />
          <Detail icon={Target} label="Target duration" value={`${current.target_duration} months`} />
          <Detail icon={Globe} label="Language" value={labelFor(LANGUAGES, current.language)} />
          <Detail icon={MapPin} label="Location" value={[current.country, current.timezone].filter(Boolean).join(" · ") || "Not set"} />
          <Detail icon={Target} label="Your goal" value={current.learning_goal || "Not set"} wide />
        </div>
      )}
    </div>
  );
}
