from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.notification_repository import (
    NotificationRepository,
    PushSubscriptionRepository,
)
from app.repositories.profile_repository import ProfileRepository
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    PushSubscribeRequest,
)


class NotificationService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repository = ProfileRepository(db)
        self.notifications = NotificationRepository(db)
        self.subscriptions = PushSubscriptionRepository(db)

    async def _profile(self, auth_user_id: UUID):
        profile = await self.profile_repository.get_by_auth_user_id(
            auth_user_id
        )

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        return profile

    async def list(
        self,
        auth_user_id: UUID,
        limit: int = 30,
        before: datetime | None = None,
        unread_only: bool = False,
    ) -> NotificationListResponse:
        profile = await self._profile(auth_user_id)

        # One extra row tells whether there is a next page.
        rows = await self.notifications.list_for_profile(
            profile.id, limit + 1, before, unread_only
        )
        has_more = len(rows) > limit
        rows = rows[:limit]

        return NotificationListResponse(
            notifications=[
                NotificationResponse(
                    id=row.id,
                    type=row.type,
                    title=row.title,
                    body=row.body,
                    url=row.url,
                    read=row.read_at is not None,
                    created_at=row.created_at,
                )
                for row in rows
            ],
            unread_count=await self.notifications.unread_count(profile.id),
            has_more=has_more,
        )

    async def mark_read(
        self,
        auth_user_id: UUID,
        notification_id: UUID | None,
    ) -> None:
        profile = await self._profile(auth_user_id)

        try:
            await self.notifications.mark_read(profile.id, notification_id)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    def public_key(self) -> str | None:
        return settings.VAPID_PUBLIC_KEY or None

    async def subscribe(
        self,
        auth_user_id: UUID,
        payload: PushSubscribeRequest,
    ) -> None:
        profile = await self._profile(auth_user_id)

        try:
            await self.subscriptions.upsert(
                profile_id=profile.id,
                endpoint=payload.endpoint,
                p256dh=payload.keys.p256dh,
                auth=payload.keys.auth,
            )
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    async def unsubscribe(
        self,
        auth_user_id: UUID,
        endpoint: str,
    ) -> None:
        profile = await self._profile(auth_user_id)

        try:
            await self.subscriptions.delete(profile.id, endpoint)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
