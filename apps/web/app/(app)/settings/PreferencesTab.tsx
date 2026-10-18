"use client";

import { useTimezones } from "@/lib/use-timezones";
import { UserSettings } from "@/types/api";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import NativeSelect from "@/components/shared/NativeSelect";

import PushToggle from "./PushToggle";

type ToggleKey = "learning_reminders" | "ai_mentor_enabled" | "show_on_leaderboard";

const TOGGLES: { key: ToggleKey; label: string; hint: string }[] = [
  {
    key: "learning_reminders",
    label: "Daily learning reminders",
    hint: "A nudge at your reminder time on days you haven't studied yet.",
  },
  {
    key: "ai_mentor_enabled",
    label: "AI mentor",
    hint: "Turn the AI mentor chat on or off. When off, the mentor page is disabled.",
  },
  {
    key: "show_on_leaderboard",
    label: "Show me on the leaderboard",
    hint: "Others see your first name, last initial and XP. Off by default.",
  },
];

export default function PreferencesTab({
  settings,
  onUpdate,
}: {
  settings: UserSettings | null;
  onUpdate: (patch: Partial<UserSettings>) => void;
}) {
  const { options: timezones, device } = useTimezones(settings?.timezone);

  if (!settings) {
    return (
      <Card className="max-w-xl p-7">
        <h2 className="text-sm font-semibold">Preferences</h2>
        <p className="mt-3 text-sm text-muted-foreground">
          Preferences are unavailable right now. Refresh the page to try again.
        </p>
      </Card>
    );
  }

  const differsFromDevice = !!device && device !== settings.timezone;

  return (
    <Card className="max-w-xl gap-0 p-7">
      <h2 className="text-sm font-semibold">Preferences</h2>

      <div className="mt-5 space-y-5">
        {TOGGLES.map(({ key, label, hint }) => (
          <label
            key={key}
            className="flex cursor-pointer items-start justify-between gap-4"
          >
            <span className="min-w-0">
              <span className="block text-sm font-medium">{label}</span>
              <span className="block text-xs text-muted-foreground">{hint}</span>
            </span>
            <input
              type="checkbox"
              className="mt-1 size-4 shrink-0 accent-brand-violet"
              checked={settings[key]}
              onChange={(e) => onUpdate({ [key]: e.target.checked })}
            />
          </label>
        ))}

        <label className="flex items-start justify-between gap-4 opacity-60">
          <span className="min-w-0">
            <span className="block text-sm font-medium">
              Email notifications{" "}
              <span className="ml-1 rounded-full bg-muted px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide">
                Coming soon
              </span>
            </span>
            <span className="block text-xs text-muted-foreground">
              Uraan AI doesn&apos;t send emails yet. Reminders arrive in the app
              and as push notifications.
            </span>
          </span>
          <input
            type="checkbox"
            disabled
            className="mt-1 size-4 shrink-0"
            checked={false}
            readOnly
          />
        </label>

        <PushToggle />

        <div className="grid gap-4 border-t pt-5 sm:grid-cols-2">
          <div className="min-w-0 space-y-1.5">
            <Label htmlFor="reminderTime">Reminder time</Label>
            <Input
              id="reminderTime"
              type="time"
              value={settings.reminder_time.slice(0, 5)}
              disabled={!settings.learning_reminders}
              onChange={(e) =>
                e.target.value && onUpdate({ reminder_time: e.target.value })
              }
            />
          </div>

          <div className="min-w-0 space-y-1.5">
            <Label htmlFor="timezone">Timezone</Label>
            <NativeSelect
              id="timezone"
              value={settings.timezone}
              onChange={(e) => onUpdate({ timezone: e.target.value })}
            >
              {timezones.map((z) => (
                <option key={z} value={z}>
                  {z}
                </option>
              ))}
            </NativeSelect>
          </div>
        </div>

        <p className="text-xs text-muted-foreground">
          Reminders are sent at your reminder time in this timezone. Your streak
          also counts days in this timezone.
        </p>

        {differsFromDevice && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => onUpdate({ timezone: device })}
          >
            Use my device timezone ({device})
          </Button>
        )}
      </div>
    </Card>
  );
}
