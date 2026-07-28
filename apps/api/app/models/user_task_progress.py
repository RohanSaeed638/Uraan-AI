from sqlalchemy import Boolean, ForeignKey, Integer, DateTime
from sqlalchemy.orm import mapped_column

from app.models.base_model import BaseModel

class UserTaskProgress(BaseModel):

    __tablename__ = "user_task_progress"

    profile_id = mapped_column(
        ForeignKey("profiles.id")
    )

    task_id = mapped_column(
        ForeignKey("roadmap_tasks.id")
    )

    completed = mapped_column(
        Boolean,
        default=False,
    )

    completed_at = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    score = mapped_column(
        Integer,
        nullable=True,
    )