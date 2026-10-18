"use client";

import { useState } from "react";
import { User } from "@supabase/supabase-js";
import { toast } from "sonner";
import { User as UserIcon, Palette, Bell } from "lucide-react";

import { authService } from "@/services/auth/auth";
import { useAuthStore } from "@/store/auth";
import { api } from "@/lib/api";
import { UserSettings } from "@/types/api";

import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import LoadingButton from "@/components/shared/LoadingButton";
import ThemeToggle from "@/components/shared/ThemeToggle";
import { cn } from "@/lib/utils";

const tabs = [
  { key: "account", label: "Account", icon: UserIcon },
  { key: "appearance", label: "Appearance", icon: Palette },
  { key: "preferences", label: "Preferences", icon: Bell },
] as const;

type PreferenceKey =
  | "email_notifications"
  | "learning_reminders"
  | "ai_mentor_enabled";

const preferenceOptions: { key: PreferenceKey; label: string; hint: string }[] =
  [
    {
      key: "email_notifications",
      label: "Email notifications",
      hint: "Product updates and activity summaries.",
    },
    {
      key: "learning_reminders",
      label: "Learning reminders",
      hint: "A daily nudge to keep your streak going.",
    },
    {
      key: "ai_mentor_enabled",
      label: "AI mentor",
      hint: "Enable the AI mentor across the app.",
    },
  ];

export default function SettingsClient({
  user,
  settings: initialSettings,
}: {
  user: User;
  settings: UserSettings | null;
}) {
  const [settings, setSettings] = useState(initialSettings);

  async function updateSettings(patch: Partial<UserSettings>) {
    if (!settings) return;
    const previous = settings;
    setSettings({ ...settings, ...patch });
    try {
      const { data } = await api.patch<UserSettings>("/settings", patch);
      setSettings(data);
    } catch {
      setSettings(previous);
      toast.error("Could not save your preferences.");
    }
  }

  const setUser = useAuthStore((state) => state.setUser);
  const [active, setActive] = useState<(typeof tabs)[number]["key"]>(
    "account"
  );
  const [fullName, setFullName] = useState(
    user.user_metadata?.full_name ?? ""
  );
  const [saving, setSaving] = useState(false);

  const initials = (fullName || user.email || "U")
    .split(" ")
    .map((n: string) => n[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const { data, error } = await authService.updateFullName(fullName);
      if (error) {
        toast.error(error.message);
        return;
      }
      if (data.user) setUser(data.user);
      toast.success("Profile updated.");
    } catch {
      toast.error("Something went wrong.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <h1 className="font-heading text-3xl font-bold">Settings</h1>
      <p className="mt-1 text-muted-foreground">
        Manage your account and preferences.
      </p>

      <div className="mt-8 grid gap-6 lg:grid-cols-[200px_1fr]">
        <nav className="flex gap-1 lg:flex-col">
          {tabs.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActive(key)}
              className={cn(
                "flex items-center gap-2.5 rounded-xl px-3.5 py-2.5 text-left text-sm font-medium transition",
                active === key
                  ? "bg-brand-violet/10 text-brand-violet"
                  : "text-muted-foreground hover:bg-muted"
              )}
            >
              <Icon size={16} /> {label}
            </button>
          ))}
        </nav>

        <div>
          {active === "account" && (
            <Card className="max-w-xl p-7">
              <h2 className="text-sm font-semibold">Profile Information</h2>

              <div className="mt-5 flex items-center gap-4">
                <Avatar size="lg">
                  <AvatarImage src={user.user_metadata?.avatar_url} />
                  <AvatarFallback className="bg-brand-violet text-white">
                    {initials}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="text-sm font-medium">
                    {fullName || "Your name"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {user.email}
                  </p>
                </div>
              </div>

              <form onSubmit={handleSave} className="mt-6 space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="fullName">Full name</Label>
                  <Input
                    id="fullName"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" value={user.email ?? ""} disabled />
                  <p className="text-xs text-muted-foreground">
                    Contact support to change your email address.
                  </p>
                </div>

                <LoadingButton type="submit" loading={saving}>
                  Save Changes
                </LoadingButton>
              </form>
            </Card>
          )}

          {active === "preferences" && (
            <Card className="max-w-xl p-7">
              <h2 className="text-sm font-semibold">Preferences</h2>
              {settings ? (
                <div className="mt-5 space-y-5">
                  {preferenceOptions.map(({ key, label, hint }) => (
                    <label
                      key={key}
                      className="flex cursor-pointer items-start justify-between gap-4"
                    >
                      <span>
                        <span className="block text-sm font-medium">
                          {label}
                        </span>
                        <span className="block text-xs text-muted-foreground">
                          {hint}
                        </span>
                      </span>
                      <input
                        type="checkbox"
                        className="mt-1 size-4 accent-brand-violet"
                        checked={settings[key]}
                        onChange={(e) =>
                          updateSettings({ [key]: e.target.checked })
                        }
                      />
                    </label>
                  ))}

                  <div className="space-y-1.5">
                    <Label htmlFor="reminderTime">Reminder time</Label>
                    <Input
                      id="reminderTime"
                      type="time"
                      value={settings.reminder_time.slice(0, 5)}
                      disabled={!settings.learning_reminders}
                      onChange={(e) =>
                        e.target.value &&
                        updateSettings({ reminder_time: e.target.value })
                      }
                    />
                  </div>
                </div>
              ) : (
                <p className="mt-3 text-sm text-muted-foreground">
                  Preferences are unavailable right now.
                </p>
              )}
            </Card>
          )}

          {active === "appearance" && (
            <Card className="max-w-xl p-7">
              <h2 className="text-sm font-semibold">Appearance</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Choose how Uraan AI looks on this device.
              </p>
              <div className="mt-5">
                <ThemeToggle />
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
