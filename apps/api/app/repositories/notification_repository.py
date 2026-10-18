from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.push_subscription import PushSubscription


class NotificationRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_once(
        self,
        profile_id: UUID,
        type: str,
        title: str,
        body: str,
        url: str | None,
        dedupe_key: str,
    ) -> UUID | None:
        """Creates the notification unless this (profile, type, key) already
        exists. Returns its id when created, otherwise None."""
        stmt = (
            insert(Notification)
            .values(
                profile_id=profile_id,
                type=type,
                title=title,
                body=body,
                url=url,
                dedupe_key=dedupe_key,
            )
            .on_conflict_do_nothing(constraint="uq_notification_once")
            .returning(Notification.id)
        )

        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_for_profile(
        self,
        profile_id: UUID,
        limit: int = 30,
    ) -> list[Notification]:
        result = await self.db.execute(
            select(Notification)
            .where(Notification.profile_id == profile_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )

        return list(result.scalars().all())

    async def unread_count(self, profile_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.profile_id == profile_id,
                Notification.read_at.is_(None),
            )
        )

        return int(result.scalar_one())

    async def mark_read(
        self,
        profile_id: UUID,
        notification_id: UUID | None = None,
    ) -> int:
        """Marks one notification (or all when no id) as read."""
        stmt = (
            update(Notification)
            .where(
                Notification.profile_id == profile_id,
                Notification.read_at.is_(None),
            )
            .values(read_at=datetime.now(timezone.utc))
        )

        if notification_id is not None:
            stmt = stmt.where(Notification.id == notification_id)

        result = await self.db.execute(stmt)

        return result.rowcount


class PushSubscriptionRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert(
        self,
        profile_id: UUID,
        endpoint: str,
        p256dh: str,
        auth: str,
    ) -> None:
        stmt = insert(PushSubscription).values(
            profile_id=profile_id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
        )

        # The same browser re-subscribing, or a different account signing in
        # on it, takes over the endpoint.
        stmt = stmt.on_conflict_do_update(
            index_elements=["endpoint"],
            set_={
                "profile_id": profile_id,
                "p256dh": p256dh,
                "auth": auth,
            },
        )

        await self.db.execute(stmt)

    async def delete(
        self,
        profile_id: UUID,
        endpoint: str,
    ) -> int:
        result = await self.db.execute(
            PushSubscription.__table__.delete().where(
                PushSubscription.profile_id == profile_id,
                PushSubscription.endpoint == endpoint,
            )
        )

        return result.rowcount

    async def delete_by_endpoint(self, endpoint: str) -> None:
        await self.db.execute(
            PushSubscription.__table__.delete().where(
                PushSubscription.endpoint == endpoint
            )
        )

    async def list_for_profile(
        self,
        profile_id: UUID,
    ) -> list[PushSubscription]:
        result = await self.db.execute(
            select(PushSubscription).where(
                PushSubscription.profile_id == profile_id
            )
        )

        return list(result.scalars().all())
