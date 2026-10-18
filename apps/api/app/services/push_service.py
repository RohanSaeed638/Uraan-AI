import asyncio
import json
import logging

from pywebpush import WebPushException, webpush

from app.core.config import settings
from app.models.push_subscription import PushSubscription
from app.repositories.notification_repository import (
    PushSubscriptionRepository,
)

logger = logging.getLogger(__name__)


def push_enabled() -> bool:
    return bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY)


def _send_sync(subscription: PushSubscription, payload: dict) -> None:
    webpush(
        subscription_info={
            "endpoint": subscription.endpoint,
            "keys": {
                "p256dh": subscription.p256dh,
                "auth": subscription.auth,
            },
        },
        data=json.dumps(payload),
        vapid_private_key=settings.VAPID_PRIVATE_KEY,
        vapid_claims={"sub": settings.VAPID_SUBJECT},
        ttl=60 * 60 * 12,
    )


async def send_push(
    repository: PushSubscriptionRepository,
    subscriptions: list[PushSubscription],
    title: str,
    body: str,
    url: str | None,
) -> int:
    """Sends a push to each subscription and returns how many succeeded.
    Subscriptions the push service reports gone (404/410) are removed;
    other failures are logged and never raised."""
    if not push_enabled():
        return 0

    payload = {"title": title, "body": body, "url": url or "/dashboard"}
    delivered = 0

    for subscription in subscriptions:
        try:
            await asyncio.to_thread(_send_sync, subscription, payload)
            delivered += 1

        except WebPushException as exc:
            status = getattr(exc.response, "status_code", None)

            if status in (404, 410):
                await repository.delete_by_endpoint(subscription.endpoint)
            else:
                logger.warning("Web push failed (%s): %s", status, exc)

        except Exception:
            logger.exception("Web push failed unexpectedly")

    return delivered
