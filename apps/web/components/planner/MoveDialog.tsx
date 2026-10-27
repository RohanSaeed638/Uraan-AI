"use client";

import { useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { Pin } from "lucide-react";

import { addDays, dateKey, parseDate, shortDate } from "@/lib/planner";
import { PlannedLesson } from "@/types/api";

import FilterChips from "@/components/shared/FilterChips";
import LoadingButton from "@/components/shared/LoadingButton";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

interface Props {
  lesson: PlannedLesson | null;
  today: string;
  /** The day the lesson is on now, to start the picker there. */
  currentDate: string | null;
  onClose: () => void;
  onMove: (lessonId: string, date: string) => Promise<void>;
  onUnpin: (lessonId: string) => Promise<void>;
}

const MAX_AHEAD_DAYS = 365;

export default function MoveDialog({
  lesson,
  today,
  currentDate,
  onClose,
  onMove,
  onUnpin,
}: Props) {
  const t = useTranslations("planner.move");
  const locale = useLocale();

  const start = currentDate && currentDate >= today ? currentDate : today;
  const [picked, setPicked] = useState(start);
  const [saving, setSaving] = useState(false);

  const base = parseDate(today);
  const quick = [
    { value: today, label: t("today") },
    { value: dateKey(addDays(base, 1)), label: t("tomorrow") },
    { value: dateKey(addDays(base, 7)), label: t("nextWeek") },
  ];

  async function run(action: () => Promise<void>) {
    setSaving(true);

    try {
      await action();
    } finally {
      setSaving(false);
    }
  }

  const valid = picked >= today && picked <= dateKey(addDays(base, MAX_AHEAD_DAYS));

  return (
    <Dialog open={lesson !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        {lesson && (
          <>
            <DialogHeader>
              <DialogTitle>{t("title")}</DialogTitle>
              <DialogDescription className="break-words">{lesson.title}</DialogDescription>
            </DialogHeader>

            <div className="space-y-4">
              <FilterChips
                label={t("quick")}
                size="sm"
                value={quick.some((q) => q.value === picked) ? picked : ""}
                onChange={setPicked}
                options={quick}
              />

              <div className="space-y-2">
                <label htmlFor="move-date" className="text-sm font-medium">
                  {t("pick")}
                </label>
                <Input
                  id="move-date"
                  type="date"
                  min={today}
                  max={dateKey(addDays(base, MAX_AHEAD_DAYS))}
                  value={picked}
                  onChange={(e) => setPicked(e.target.value)}
                />
                {valid && (
                  <p className="text-xs text-muted-foreground">
                    {t("willStay", { date: shortDate(parseDate(picked), locale) })}
                  </p>
                )}
              </div>

              <div className="flex flex-wrap gap-2">
                <LoadingButton
                  loading={saving}
                  disabled={!valid}
                  onClick={() => run(() => onMove(lesson.id, picked))}
                  className="gap-2"
                >
                  <Pin size={14} /> {t("confirm")}
                </LoadingButton>

                {lesson.pinned && (
                  <Button
                    variant="outline"
                    disabled={saving}
                    onClick={() => run(() => onUnpin(lesson.id))}
                  >
                    {t("auto")}
                  </Button>
                )}

                <Button variant="ghost" disabled={saving} onClick={onClose}>
                  {t("cancel")}
                </Button>
              </div>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
