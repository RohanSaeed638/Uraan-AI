from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import mapped_column

from app.models.base_model import BaseModel

class ChatMessage(BaseModel):

    __tablename__ = "chat_messages"

    profile_id = mapped_column(
        ForeignKey("profiles.id")
    )

    task_id = mapped_column(
        ForeignKey("roadmap_tasks.id"),
        nullable=True,
    )

    role = mapped_column(
        String(20)
    )

    message = mapped_column(Text)