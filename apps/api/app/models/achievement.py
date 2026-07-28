from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import  mapped_column

from app.models.base_model import BaseModel

class Achievement(BaseModel):

    __tablename__ = "achievements"

    profile_id = mapped_column(
        ForeignKey("profiles.id")
    )

    title = mapped_column(String(100))

    description = mapped_column(Text)

    unlocked = mapped_column(
        Boolean,
        default=False,
    )