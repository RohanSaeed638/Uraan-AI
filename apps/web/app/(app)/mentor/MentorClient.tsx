"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, Code2, Loader2, MessageSquarePlus, Send, Trash2 } from "lucide-react";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import {
  createConversation,
  deleteConversation,
  getConversation,
  getSuggestions,
  listConversations,
  sendMessage,
} from "@/lib/api/mentor";
import { apiErrorMessage } from "@/lib/profile-options";
import { MentorChip, MentorConversationDetail, MentorMessage } from "@/types/api";

import ReviewDialog from "@/components/mentor/ReviewDialog";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

const LIST_KEY = ["mentor", "conversations"] as const;
const detailKey = (id: string) => ["mentor", "conversation", id] as const;

export default function MentorClient() {
  const t = useTranslations("mentorChat");
  const queryClient = useQueryClient();
  const [reviewOpen, setReviewOpen] = useState(false);

  // Suggestions come from the learner's own roadmap; the chat works without them.
  const suggestions = useQuery({
    queryKey: ["mentor", "suggestions"],
    queryFn: getSuggestions,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  function pickChip(chip: MentorChip) {
    if (chip.kind === "review") {
      setReviewOpen(true);
    } else if (chip.prompt && !send.isPending) {
      send.mutate(chip.prompt);
    }
  }

  const [activeId, setActiveId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const conversations = useQuery({
    queryKey: LIST_KEY,
    queryFn: listConversations,
  });

  const detail = useQuery({
    queryKey: detailKey(activeId ?? ""),
    queryFn: () => getConversation(activeId!),
    enabled: !!activeId,
  });

  const send = useMutation({
    mutationFn: async (content: string) => {
      const id = activeId ?? (await createConversation()).id;
      return sendMessage(id, content);
    },
    onSuccess: (result) => {
      setDraft("");
      setActiveId(result.conversation_id);
      queryClient.setQueryData<MentorConversationDetail>(
        detailKey(result.conversation_id),
        (old) =>
          old
            ? {
                ...old,
                messages: [
                  ...old.messages,
                  result.user_message,
                  result.assistant_message,
                ],
              }
            : old
      );
      queryClient.invalidateQueries({
        queryKey: detailKey(result.conversation_id),
      });
      queryClient.invalidateQueries({ queryKey: LIST_KEY });
    },
    onError: (e) =>
      toast.error(apiErrorMessage(e, t("replyFailed"))),
  });

  const remove = useMutation({
    mutationFn: deleteConversation,
    onSuccess: (_, id) => {
      if (id === activeId) setActiveId(null);
      queryClient.invalidateQueries({ queryKey: LIST_KEY });
    },
    onError: () => toast.error(t("deleteFailed")),
  });

  const messages: MentorMessage[] = detail.data?.messages ?? [];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, send.isPending]);

  function submit(e: React.SyntheticEvent) {
    e.preventDefault();
    const content = draft.trim();
    if (!content || send.isPending) return;
    send.mutate(content);
  }

  return (
    <div className="grid h-[calc(100vh-8rem)] grid-cols-1 grid-rows-[auto_minmax(0,1fr)] gap-6 lg:grid-cols-[280px_minmax(0,1fr)] lg:grid-rows-1">
      <Card className="flex max-h-44 flex-col gap-3 overflow-hidden p-4 lg:max-h-none">
        <Button
          variant="outline"
          className="gap-2"
          onClick={() => {
            setActiveId(null);
            setDraft("");
          }}
        >
          <MessageSquarePlus size={15} /> {t("new")}
        </Button>

        <div className="-mx-1 flex-1 space-y-1 overflow-y-auto px-1">
          {conversations.isLoading && (
            <p className="p-2 text-sm text-muted-foreground">{t("loading")}</p>
          )}
          {conversations.data?.length === 0 && (
            <p className="p-2 text-sm text-muted-foreground">
              {t("none")}
            </p>
          )}
          {conversations.data?.map((c) => (
            <div
              key={c.id}
              className={cn(
                "group flex items-center gap-1 rounded-xl pe-1 transition",
                c.id === activeId
                  ? "bg-brand-gold/15 text-brand-gold-deep dark:text-brand-gold"
                  : "hover:bg-muted"
              )}
            >
              <button
                onClick={() => setActiveId(c.id)}
                className="min-w-0 flex-1 truncate px-3 py-2 text-start text-sm font-medium"
              >
                {c.title}
              </button>
              <button
                aria-label={t("delete")}
                onClick={() => remove.mutate(c.id)}
                className="rounded-lg p-1.5 text-muted-foreground opacity-0 transition hover:text-destructive group-hover:opacity-100 focus:opacity-100"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      </Card>

      <Card className="flex flex-col overflow-hidden p-0">
        <div role="region" aria-label={t("title")} tabIndex={0} className="flex-1 space-y-4 overflow-y-auto p-6 focus-visible:outline-2 focus-visible:outline-ring">
          {messages.length === 0 && !send.isPending && (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <span className="flex size-14 items-center justify-center rounded-full bg-brand-violet/10">
                <Bot className="size-6 text-brand-violet" />
              </span>
              <h1 className="font-heading mt-4 text-xl font-bold">
                {t("title")}
              </h1>
              <p className="mt-1 max-w-sm text-sm text-muted-foreground">
                {t("intro")}
              </p>
            </div>
          )}

          {messages.map((m) => (
            <div
              key={m.id}
              className={cn(
                "flex",
                m.role === "user" ? "justify-end" : "justify-start"
              )}
            >
              <p
                className={cn(
                  "max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm",
                  m.role === "user"
                    ? "bg-brand-violet text-white"
                    : "bg-muted"
                )}
              >
                {m.content}
              </p>
            </div>
          ))}

          {send.isPending && (
            <>
              <div className="flex justify-end">
                <p className="max-w-[80%] whitespace-pre-wrap rounded-2xl bg-brand-violet px-4 py-2.5 text-sm text-white">
                  {send.variables}
                </p>
              </div>
              <div className="flex justify-start">
                <p className="flex items-center gap-2 rounded-2xl bg-muted px-4 py-2.5 text-sm text-muted-foreground">
                  <Loader2 size={14} className="animate-spin" /> {t("thinking")}
                </p>
              </div>
            </>
          )}
          <div ref={bottomRef} />
        </div>

        {(suggestions.data?.length ?? 0) > 0 && (
          <div
            className="flex flex-wrap gap-2 border-t px-4 pt-3"
            aria-label={t("suggestions")}
          >
            {suggestions.data!.map((chip) => (
              <button
                key={chip.id}
                type="button"
                disabled={send.isPending}
                onClick={() => pickChip(chip)}
                className="inline-flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition hover:bg-muted disabled:opacity-50"
              >
                {chip.kind === "review" && <Code2 size={13} />}
                <span className="max-w-60 truncate">{chip.label}</span>
              </button>
            ))}
          </div>
        )}

        <form onSubmit={submit} className="flex items-end gap-3 border-t p-4">
          <Textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) submit(e);
            }}
            placeholder={t("placeholder")}
            rows={1}
            maxLength={8000}
            className="max-h-40 min-h-10 resize-none"
          />
          <Button
            type="submit"
            size="icon"
            disabled={!draft.trim() || send.isPending}
            aria-label={t("send")}
          >
            <Send size={16} />
          </Button>
        </form>
      </Card>
      <ReviewDialog open={reviewOpen} onOpenChange={setReviewOpen} />
    </div>
  );
}
