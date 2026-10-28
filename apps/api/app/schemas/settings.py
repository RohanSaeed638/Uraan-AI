from datetime import time
from enum import Enum
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, ConfigDict, computed_field, field_validator


class ThemePreference(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class Wording(str, Enum):
    CLASSIC = "classic"
    GAMIFIED = "gamified"


class AiTone(str, Enum):
    FRIENDLY = "friendly"
    GENZ = "genz"
    PROFESSIONAL = "professional"


class UserSettingsResponse(BaseModel):
    id: UUID
    profile_id: UUID

    theme: ThemePreference
    email_notifications: bool
    learning_reminders: bool
    reminder_time: time
    timezone: str
    ai_mentor_enabled: bool
    ai_tone: AiTone = AiTone.FRIENDLY
    wording: Wording = Wording.CLASSIC
    show_on_leaderboard: bool

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def email_available(self) -> bool:
        """Whether this server can send email at all (a sender is configured)."""
        from app.services.email_service import email_available

        return email_available()


class UpdateUserSettingsRequest(BaseModel):
    theme: ThemePreference | None = None
    email_notifications: bool | None = None
    learning_reminders: bool | None = None
    reminder_time: time | None = None
    timezone: str | None = None
    ai_mentor_enabled: bool | None = None
    ai_tone: AiTone | None = None
    wording: Wording | None = None
    show_on_leaderboard: bool | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None):
        if value is None:
            return value

        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError:
            raise ValueError("Invalid IANA timezone")

        return value

    @field_validator(
        "theme",
        "email_notifications",
        "learning_reminders",
        "reminder_time",
        "timezone",
        "ai_mentor_enabled",
        "ai_tone",
        "wording",
        "show_on_leaderboard",
    )
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Null values are not allowed")
        return value

    @field_validator("reminder_time")
    @classmethod
    def validate_reminder_time(cls, value: time | None):
        if value is not None and value.tzinfo is not None:
            raise ValueError(
                "Reminder time must not include a timezone offset"
            )
        return value    

