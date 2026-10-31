"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { Megaphone } from "lucide-react";
import { toast } from "sonner";

import { listAnnouncements, publishAnnouncement, updateAnnouncement } from "@/lib/api/admin";
import { apiErrorMessage } from "@/lib/profile-options";

import EmptyState from "@/components/shared/EmptyState";
import LoadingButton from "@/components/shared/LoadingButton";
import NativeSelect from "@/components/shared/NativeSelect";
import Pill from "@/components/shared/Pill";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export default function AdminAnnouncementsPage() {
  const t = useTranslations("admin.announcements");
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [level, setLevel] = useState<"info" | "warning">("info");
  const [ends, setEnds] = useState("");
  const [notify, setNotify] = useState(false);

  const list = useQuery({ queryKey: ["admin", "announcements"], queryFn: listAnnouncements });
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["admin", "announcements"] });

  const publish = useMutation({
    mutationFn: () =>
      publishAnnouncement({
        title,
        body,
        level,
        ends_at: ends ? new Date(ends).toISOString() : null,
        notify,
      }),
    onSuccess: (row) => {
      toast.success(notify ? t("publishedNotified", { count: row.notified }) : t("published"));
      setTitle("");
      setBody("");
      setEnds("");
      setNotify(false);
      refresh();
    },
    onError: (error) => toast.error(apiErrorMessage(error, t("failed"))),
  });

  const toggle = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) => updateAnnouncement(id, { is_active: active }),
    onSuccess: refresh,
    onError: (error) => toast.error(apiErrorMessage(error, t("failed"))),
  });

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
      <Card className="h-fit gap-4 p-6">
        <h2 className="font-heading text-lg font-semibold">{t("newTitle")}</h2>

        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            publish.mutate();
          }}
        >
          <div className="space-y-1.5">
            <Label htmlFor="a-title">{t("title")}</Label>
            <Input id="a-title" required minLength={2} maxLength={160} value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="a-body">{t("body")}</Label>
            <Textarea id="a-body" required minLength={2} maxLength={2000} className="min-h-24" value={body} onChange={(e) => setBody(e.target.value)} />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="a-level">{t("level")}</Label>
              <NativeSelect id="a-level" value={level} onChange={(e) => setLevel(e.target.value as "info" | "warning")}>
                <option value="info">{t("info")}</option>
                <option value="warning">{t("warning")}</option>
              </NativeSelect>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="a-ends">{t("ends")}</Label>
              <Input id="a-ends" type="datetime-local" value={ends} onChange={(e) => setEnds(e.target.value)} />
            </div>
          </div>
          <label className="flex cursor-pointer items-start gap-3 text-sm">
            <input type="checkbox" className="mt-1 size-4 accent-gold" checked={notify} onChange={(e) => setNotify(e.target.checked)} />
            <span>
              <span className="font-medium">{t("notify")}</span>
              <span className="block text-xs text-muted-foreground">{t("notifyHint")}</span>
            </span>
          </label>
          <LoadingButton type="submit" loading={publish.isPending}>{t("publish")}</LoadingButton>
        </form>
      </Card>

      <div className="space-y-3">
        <h2 className="font-heading text-lg font-semibold">{t("history")}</h2>

        {list.isError ? (
          <EmptyState icon={Megaphone} title={t("loadFailed")} />
        ) : (list.data ?? []).length === 0 ? (
          <EmptyState icon={Megaphone} title={t("none")} text={t("noneText")} />
        ) : (
          (list.data ?? []).map((a) => {
            const over = a.ends_at !== null && new Date(a.ends_at) <= new Date();

            return (
              <Card key={a.id} className="gap-2 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="break-words font-semibold">{a.title}</p>
                    <p className="mt-1 break-words text-sm text-muted-foreground">{a.body}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <Pill tone={a.level === "warning" ? "gold" : "soft"}>{t(a.level)}</Pill>
                    <Pill tone={a.is_active && !over ? "gold" : "soft"}>
                      {over ? t("ended") : a.is_active ? t("live") : t("off")}
                    </Pill>
                  </div>
                </div>
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
                  <span>
                    {a.created_at.slice(0, 10)}
                    {a.notified > 0 && ` · ${t("notifiedCount", { count: a.notified })}`}
                    {a.ends_at && ` · ${t("until", { date: a.ends_at.slice(0, 16).replace("T", " ") })}`}
                  </span>
                  {!over && (
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={toggle.isPending}
                      onClick={() => toggle.mutate({ id: a.id, active: !a.is_active })}
                    >
                      {a.is_active ? t("switchOff") : t("switchOn")}
                    </Button>
                  )}
                </div>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
}
