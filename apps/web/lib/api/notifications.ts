import { api } from "./client";
import { NotificationList } from "@/types/api";

export interface NotificationQuery {
  limit?: number;
  /** created_at of the last one already shown: continues after it. */
  before?: string;
  unread?: boolean;
}

export async function listNotifications(params: NotificationQuery = {}) {
  const { data } = await api.get<NotificationList>("/notifications", { params });
  return data;
}

export async function markNotificationRead(id: string) {
  await api.patch(`/notifications/${id}/read`);
}

export async function markAllNotificationsRead() {
  await api.post("/notifications/read-all");
}

export async function getPushPublicKey() {
  const { data } = await api.get<{ public_key: string | null }>(
    "/push/public-key"
  );
  return data.public_key;
}

export async function savePushSubscription(subscription: PushSubscriptionJSON) {
  await api.post("/push/subscriptions", {
    endpoint: subscription.endpoint,
    keys: subscription.keys,
  });
}

export async function deletePushSubscription(endpoint: string) {
  await api.post("/push/subscriptions/delete", { endpoint });
}
