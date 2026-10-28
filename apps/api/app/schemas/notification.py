from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    id: UUID
    type: str
    title: str
    body: str
    url: str | None = None
    read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    unread_count: int
    # More older ones exist: ask again with `before` set to the last created_at.
    has_more: bool = False


class PushKeys(BaseModel):
    p256dh: str = Field(min_length=1, max_length=255)
    auth: str = Field(min_length=1, max_length=255)


class PushSubscribeRequest(BaseModel):
    endpoint: str = Field(min_length=1, max_length=2000)
    keys: PushKeys


class PushUnsubscribeRequest(BaseModel):
    endpoint: str = Field(min_length=1, max_length=2000)


class PushPublicKeyResponse(BaseModel):
    public_key: str | None = None
