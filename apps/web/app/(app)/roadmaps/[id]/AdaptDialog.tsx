"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

import { apiErrorMessage } from "@/lib/profile-options";
import { AdaptReason, AdaptRequest } from "@/types/roadmap";

import NativeSelect from "@/components/shared/NativeSelect";
import LoadingButton from "@/components/shared/LoadingButton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentHours: number;
  onSubmit: (request: AdaptRequest) => Promise<void>;
}

const REASONS: AdaptReason[] = ["study_time", "behind", "goal"];

export default function AdaptDialog({
  open,
  onOpenChange,
  currentHours,
  onSubmit,
}: Props) {
  const t = useTranslations("roadmapEngine.adapt");

  const [reason, setReason] = useState<AdaptReason>("study_time");
  const [hours, setHours] = useState(String(currentHours));
  const [months, setMonths] = useState("");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();

    const dailyHours = Number(hours);
    const monthsLeft = months.trim() === "" ? undefined : Number(months);

    if (!Number.isInteger(dailyHours) || dailyHours < 1 || dailyHours > 12) {
      setError(t("hoursInvalid"));
      return;
    }

    if (
      monthsLeft !== undefined &&
      (!Number.isInteger(monthsLeft) || monthsLeft < 1 || monthsLeft > 36)
    ) {
      setError(t("monthsInvalid"));
      return;
    }

    setSaving(true);
    setError(null);

    try {
      await onSubmit({
        reason,
        daily_hours: dailyHours,
        months_left: monthsLeft,
        note: note.trim() || undefined,
      });
      onOpenChange(false);
    } catch (err) {
      setError(apiErrorMessage(err, t("failed")));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("title")}</DialogTitle>
          <DialogDescription>{t("description")}</DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="adapt-reason" className="text-sm font-medium">
              {t("reason")}
            </label>
            <NativeSelect
              id="adapt-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value as AdaptReason)}
            >
              {REASONS.map((r) => (
                <option key={r} value={r}>
                  {t(`reasons.${r}`)}
                </option>
              ))}
            </NativeSelect>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label htmlFor="adapt-hours" className="text-sm font-medium">
                {t("hours")}
              </label>
              <Input
                id="adapt-hours"
                type="number"
                inputMode="numeric"
                min={1}
                max={12}
                value={hours}
                onChange={(e) => setHours(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="adapt-months" className="text-sm font-medium">
                {t("months")}
              </label>
              <Input
                id="adapt-months"
                type="number"
                inputMode="numeric"
                min={1}
                max={36}
                placeholder={t("monthsPlaceholder")}
                value={months}
                onChange={(e) => setMonths(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="adapt-note" className="text-sm font-medium">
              {t("note")}
            </label>
            <Textarea
              id="adapt-note"
              value={note}
              maxLength={300}
              placeholder={t("notePlaceholder")}
              className="min-h-20"
              onChange={(e) => setNote(e.target.value)}
            />
          </div>

          <p className="text-xs text-muted-foreground">{t("safe")}</p>

          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}

          <LoadingButton type="submit" loading={saving}>
            {t("submit")}
          </LoadingButton>
        </form>
      </DialogContent>
    </Dialog>
  );
}
