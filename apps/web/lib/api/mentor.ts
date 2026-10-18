import { api } from "./client";
import {
  MentorConversation,
  MentorConversationDetail,
  MentorConversationList,
  MentorSendResult,
} from "@/types/api";

export async function listConversations() {
  const { data } = await api.get<MentorConversationList>(
    "/mentor/conversations",
    { params: { page_size: 100 } }
  );
  return data.conversations;
}

export async function getConversation(id: string) {
  const { data } = await api.get<MentorConversationDetail>(
    `/mentor/conversations/${id}`
  );
  return data;
}

export async function createConversation(title?: string) {
  const { data } = await api.post<MentorConversation>(
    "/mentor/conversations",
    title ? { title } : {}
  );
  return data;
}

export async function sendMessage(conversationId: string, content: string) {
  const { data } = await api.post<MentorSendResult>(
    `/mentor/conversations/${conversationId}/messages`,
    { content }
  );
  return data;
}

export async function deleteConversation(id: string) {
  await api.delete(`/mentor/conversations/${id}`);
}
