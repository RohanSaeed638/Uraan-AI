"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, Loader2, MessageSquarePlus, Send, Trash2 } from "lucide-react";
import { toast } from "sonner";

import {
  createConversation,
  deleteConversation,
  getConversation,
  listConversations,
  sendMessage,
} from "@/lib/api/mentor";
import { MentorConversationDetail, MentorMessage } from "@/types/api";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

const LIST_KEY = ["mentor", "conversations"] as const;
const detailKey = (id: string) => ["mentor", "conversation", id] as const;

export default function MentorClient() {
  const queryClient = useQueryClient();
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
    onError: () => toast.error("The mentor couldn't reply. Try again."),
  });

  const remove = useMutation({
    mutationFn: deleteConversation,
    onSuccess: (_, id) => {
      if (id === activeId) setActiveId(null);
      queryClient.invalidateQueries({ queryKey: LIST_KEY });
    },
    onError: () => toast.error("Couldn't delete the conversation."),
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
    <div className="grid h-[calc(100vh-8rem)] gap-6 lg:grid-cols-[280px_1fr]">
      <Card className="flex flex-col gap-3 overflow-hidden p-4">
        <Button
          variant="outline"
          className="gap-2"
          onClick={() => {
            setActiveId(null);
            setDraft("");
          }}
        >
          <MessageSquarePlus size={15} /> New conversation
        </Button>

        <div className="-mx-1 flex-1 space-y-1 overflow-y-auto px-1">
          {conversations.isLoading && (
            <p className="p-2 text-sm text-muted-foreground">Loading…</p>
          )}
          {conversations.data?.length === 0 && (
            <p className="p-2 text-sm text-muted-foreground">
              No conversations yet.
            </p>
          )}
          {conversations.data?.map((c) => (
            <div
              key={c.id}
              className={cn(
                "group flex items-center gap-1 rounded-xl pr-1 transition",
                c.id === activeId
                  ? "bg-brand-violet/10 text-brand-violet"
                  : "hover:bg-muted"
              )}
            >
              <button
                onClick={() => setActiveId(c.id)}
                className="min-w-0 flex-1 truncate px-3 py-2 text-left text-sm font-medium"
              >
                {c.title}
              </button>
              <button
                aria-label="Delete conversation"
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
        <div className="flex-1 space-y-4 overflow-y-auto p-6">
          {messages.length === 0 && !send.isPending && (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <span className="flex size-14 items-center justify-center rounded-full bg-brand-violet/10">
                <Bot className="size-6 text-brand-violet" />
              </span>
              <h1 className="font-heading mt-4 text-xl font-bold">
                AI Mentor
              </h1>
              <p className="mt-1 max-w-sm text-sm text-muted-foreground">
                Ask about your roadmap, a concept you&apos;re stuck on, or what
                to learn next.
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
                  <Loader2 size={14} className="animate-spin" /> Thinking…
                </p>
              </div>
            </>
          )}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={submit} className="flex items-end gap-3 border-t p-4">
          <Textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) submit(e);
            }}
            placeholder="Ask your mentor…"
            rows={1}
            maxLength={8000}
            className="max-h-40 min-h-10 resize-none"
          />
          <Button
            type="submit"
            size="icon"
            disabled={!draft.trim() || send.isPending}
            aria-label="Send"
          >
            <Send size={16} />
          </Button>
        </form>
      </Card>
    </div>
  );
}
