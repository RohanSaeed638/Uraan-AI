from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.base import get_db
from app.schemas.notification import (
    NotificationListResponse,
    PushPublicKeyResponse,
    PushSubscribeRequest,
    PushUnsubscribeRequest,
)
from app.services.notification_service import NotificationService

router = APIRouter(tags=["Notifications"])


@router.get("/notifications", response_model=NotificationListResponse)
async def list_notifications(
    limit: int = Query(default=30, ge=1, le=100),
    before: datetime | None = None,
    unread: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await NotificationService(db).list(current_user.id, limit, before, unread)


@router.post(
    "/notifications/read-all",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def read_all_notifications(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    await NotificationService(db).mark_read(current_user.id, None)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/notifications/{notification_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def read_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    await NotificationService(db).mark_read(current_user.id, notification_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/push/public-key", response_model=PushPublicKeyResponse)
async def push_public_key(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return PushPublicKeyResponse(
        public_key=NotificationService(db).public_key()
    )


@router.post(
    "/push/subscriptions",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def subscribe_push(
    payload: PushSubscribeRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    await NotificationService(db).subscribe(current_user.id, payload)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/push/subscriptions/delete",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unsubscribe_push(
    payload: PushUnsubscribeRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    await NotificationService(db).unsubscribe(
        current_user.id, payload.endpoint
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
