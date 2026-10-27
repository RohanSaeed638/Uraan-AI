from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel


class UserSettings(BaseModel):
    __tablename__ = "user_settings"

    profile_id: Mapped[str] = mapped_column(
        ForeignKey(
            "profiles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    theme: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="system",
        server_default="system",
    )

    email_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    learning_reminders: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    reminder_time = mapped_column(
        Time(timezone=False),
        nullable=False,
        default=lambda: __import__("datetime").time(9, 0),
    )

    timezone: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="UTC",
        server_default="UTC",
    )

    ai_mentor_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    show_on_leaderboard: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # Plain wording ("Tasks") or game wording ("Missions"): classic or gamified.
    wording: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="classic",
        server_default="classic",
    )

    # How the AI mentor talks: friendly, genz or professional.
    ai_tone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="friendly",
        server_default="friendly",
    )
