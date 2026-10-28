"use client";

import { useTimezones } from "@/lib/use-timezones";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";

import { setWordingCookie } from "@/app/actions/locale";
import { AiTone, UserSettings, Wording } from "@/types/api";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import NativeSelect from "@/components/shared/NativeSelect";

import PushToggle from "./PushToggle";

const TONES = ["friendly", "genz", "professional"] as const;

type ToggleKey = "learning_reminders" | "ai_mentor_enabled" | "show_on_leaderboard";

const TOGGLES: ToggleKey[] = ["learning_reminders", "ai_mentor_enabled", "show_on_leaderboard"];

export default function PreferencesTab({
  settings,
  onUpdate,
}: {
  settings: UserSettings | null;
  onUpdate: (patch: Partial<UserSettings>) => void;
}) {
  const { options: timezones, device } = useTimezones(settings?.timezone);
  const t = useTranslations("mentorTone");
  const tp = useTranslations("settings.prefs");
  const router = useRouter();

  if (!settings) {
    return (
      <Card className="max-w-xl p-7">
        <h2 className="text-sm font-semibold">{tp("title")}</h2>
        <p className="mt-3 text-sm text-muted-foreground">{tp("unavailable")}</p>
      </Card>
    );
  }

  const differsFromDevice = !!device && device !== settings.timezone;

  return (
    <Card className="max-w-xl gap-0 p-7">
      <h2 className="text-sm font-semibold">{tp("title")}</h2>

      <div className="mt-5 space-y-5">
        {TOGGLES.map((key) => (
          <label
            key={key}
            className="flex cursor-pointer items-start justify-between gap-4"
          >
            <span className="min-w-0">
              <span className="block text-sm font-medium">{tp(key)}</span>
              <span className="block text-xs text-muted-foreground">{tp(`${key}_hint`)}</span>
            </span>
            <input
              type="checkbox"
              className="mt-1 size-4 shrink-0 accent-gold"
              checked={settings[key]}
              onChange={(e) => onUpdate({ [key]: e.target.checked })}
            />
          </label>
        ))}

        <div className="space-y-1.5">
          <Label htmlFor="wording">{tp("wording")}</Label>
          <NativeSelect
            id="wording"
            value={settings.wording ?? "classic"}
            onChange={async (e) => {
              const wording = e.target.value as Wording;

              onUpdate({ wording });
              await setWordingCookie(wording);
              router.refresh();
            }}
          >
            <option value="classic">{tp("classic")}</option>
            <option value="gamified">{tp("gamified")}</option>
          </NativeSelect>
          <p className="text-xs text-muted-foreground">{tp("wordingHint")}</p>
        </div>

        {settings.ai_mentor_enabled && (
          <div className="space-y-1.5">
            <Label htmlFor="aiTone">{t("tone")}</Label>
            <NativeSelect
              id="aiTone"
              value={settings.ai_tone}
              onChange={(e) => onUpdate({ ai_tone: e.target.value as AiTone })}
            >
              {TONES.map((tone) => (
                <option key={tone} value={tone}>
                  {t(`tones.${tone}`)}
                </option>
              ))}
            </NativeSelect>
            <p className="text-xs text-muted-foreground">{t("toneHint")}</p>
          </div>
        )}

        <label className="flex cursor-pointer items-start justify-between gap-4">
          <span className="min-w-0">
            <span className="block text-sm font-medium">{tp("emailOn")}</span>
            <span className="block text-xs text-muted-foreground">{tp("emailOnHint")}</span>
            {!settings.email_available && (
              <span className="mt-1 block text-xs text-amber-600 dark:text-amber-400">
                {tp("emailUnavailable")}
              </span>
            )}
          </span>
          <input
            type="checkbox"
            className="mt-1 size-4 shrink-0 accent-gold"
            checked={settings.email_notifications}
            onChange={(e) => onUpdate({ email_notifications: e.target.checked })}
          />
        </label>

        <PushToggle />

        <div className="grid gap-4 border-t pt-5 sm:grid-cols-2">
          <div className="min-w-0 space-y-1.5">
            <Label htmlFor="reminderTime">{tp("reminderTime")}</Label>
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
            <Label htmlFor="timezone">{tp("timezone")}</Label>
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
          {tp("timezoneHint")}
        </p>

        {differsFromDevice && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => onUpdate({ timezone: device })}
          >
            {tp("useDevice", { zone: device })}
          </Button>
        )}
      </div>
    </Card>
  );
}
