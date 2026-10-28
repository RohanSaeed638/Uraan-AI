import {
  deletePushSubscription,
  getPushPublicKey,
  savePushSubscription,
} from "@/lib/api/notifications";

export type PushStatus =
  | "unsupported"
  | "unconfigured"
  | "denied"
  | "off"
  | "on";

function urlBase64ToUint8Array(base64: string) {
  const padding = "=".repeat((4 - (base64.length % 4)) % 4);
  const raw = atob((base64 + padding).replace(/-/g, "+").replace(/_/g, "/"));
  return Uint8Array.from(raw, (c) => c.charCodeAt(0));
}

export function pushSupported() {
  return (
    typeof window !== "undefined" &&
    "serviceWorker" in navigator &&
    "PushManager" in window &&
    "Notification" in window
  );
}

async function currentSubscription() {
  const registration = await navigator.serviceWorker.getRegistration("/sw.js");
  return registration ? registration.pushManager.getSubscription() : null;
}

export async function getPushStatus(): Promise<PushStatus> {
  if (!pushSupported()) return "unsupported";
  if (!(await getPushPublicKey())) return "unconfigured";
  if (Notification.permission === "denied") return "denied";

  return (await currentSubscription()) ? "on" : "off";
}

export async function enablePush(): Promise<PushStatus> {
  if (!pushSupported()) return "unsupported";

  const publicKey = await getPushPublicKey();
  if (!publicKey) return "unconfigured";

  const permission = await Notification.requestPermission();
  if (permission !== "granted") {
    return permission === "denied" ? "denied" : "off";
  }

  const registration = await navigator.serviceWorker.register("/sw.js");
  await navigator.serviceWorker.ready;

  const subscription =
    (await registration.pushManager.getSubscription()) ??
    (await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(publicKey),
    }));

  await savePushSubscription(subscription.toJSON());

  return "on";
}

export async function disablePush(): Promise<PushStatus> {
  const subscription = await currentSubscription();

  if (subscription) {
    await deletePushSubscription(subscription.endpoint);
    await subscription.unsubscribe();
  }

  return "off";
}
