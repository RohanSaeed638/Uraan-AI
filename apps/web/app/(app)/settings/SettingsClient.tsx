"use client";

import { useState } from "react";
import { User } from "@supabase/supabase-js";
import { toast } from "sonner";
import { Bell, Database, Palette, User as UserIcon } from "lucide-react";

import { api } from "@/lib/api";
import { apiErrorMessage } from "@/lib/profile-options";
import { UserSettings } from "@/types/api";
import { cn } from "@/lib/utils";

import AccountTab from "./AccountTab";
import AppearanceTab from "./AppearanceTab";
import DataTab from "./DataTab";
import PreferencesTab from "./PreferencesTab";
import type { TabKey } from "./tabs";

const tabs = [
  { key: "account", label: "Account", icon: UserIcon },
  { key: "appearance", label: "Appearance", icon: Palette },
  { key: "preferences", label: "Preferences", icon: Bell },
  { key: "data", label: "Data", icon: Database },
] as const;

export default function SettingsClient({
  user,
  settings: initialSettings,
  initialTab = "account",
}: {
  user: User;
  settings: UserSettings | null;
  initialTab?: TabKey;
}) {
  const [active, setActive] = useState<TabKey>(initialTab);
  const [settings, setSettings] = useState(initialSettings);

  /** Applies a change at once, saves it, and undoes it if the save fails. */
  async function updateSettings(patch: Partial<UserSettings>) {
    if (!settings) return;

    const previous = settings;
    setSettings({ ...settings, ...patch });

    try {
      const { data } = await api.patch<UserSettings>("/settings", patch);
      setSettings(data);
    } catch (err) {
      setSettings(previous);
      toast.error(apiErrorMessage(err, "Couldn't save your preferences."));
    }
  }

  return (
    <div>
      <h1 className="font-heading text-3xl font-bold">Settings</h1>
      <p className="mt-1 text-muted-foreground">
        Manage your account and preferences.
      </p>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-[200px_minmax(0,1fr)]">
        <nav
          aria-label="Settings sections"
          className="flex gap-1 overflow-x-auto lg:flex-col lg:overflow-visible"
        >
          {tabs.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              type="button"
              onClick={() => setActive(key)}
              aria-current={active === key ? "page" : undefined}
              className={cn(
                "flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-xl px-2.5 py-2.5 text-left text-sm font-medium transition sm:gap-2.5 sm:px-3.5",
                active === key
                  ? "bg-brand-violet/10 text-brand-violet"
                  : "text-muted-foreground hover:bg-muted"
              )}
            >
              <Icon size={16} /> {label}
            </button>
          ))}
        </nav>

        <div className="min-w-0">
          {active === "account" && <AccountTab user={user} />}
          {active === "appearance" && <AppearanceTab />}
          {active === "preferences" && (
            <PreferencesTab settings={settings} onUpdate={updateSettings} />
          )}
          {active === "data" && <DataTab />}
        </div>
      </div>
    </div>
  );
}
