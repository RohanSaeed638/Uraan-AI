from datetime import datetime
from uuid6 import uuid7

from sqlalchemy import DateTime
from sqlalchemy import func

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped


class UUIDMixin:

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
    )


class TimestampMixin:

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )