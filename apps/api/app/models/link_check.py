from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel


class LinkCheck(BaseModel):
    """What was found the last time a learning link was checked (see services/link_checker.py).

    Shared by everyone: the same address is checked once, not once per learner."""

    __tablename__ = "link_checks"

    url: Mapped[str] = mapped_column(Text, unique=True)

    # ok | dead | unknown
    status: Mapped[str] = mapped_column(String(10), index=True)

    http_status: Mapped[int | None] = mapped_column(Integer)

    reason: Mapped[str | None] = mapped_column(String(120))

    # Checks in a row that found it dead (reset when it answers again).
    fail_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
