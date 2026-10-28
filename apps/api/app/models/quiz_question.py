# import uuid

# from sqlalchemy import (
#     ForeignKey,
#     Integer,
#     String,
#     Text,
#     JSON,
# )
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.orm import Mapped, mapped_column

# from app.models.base_model import BaseModel


# class QuizQuestion(BaseModel):
#     __tablename__ = "quiz_questions"

#     id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True),
#         primary_key=True,
#         default=uuid.uuid4,
#     )

#     task_id: Mapped[uuid.UUID] = mapped_column(
#         UUID(as_uuid=True),
#         ForeignKey(
#             "roadmap_tasks.id",
#             ondelete="CASCADE",
#         ),
#         nullable=False,
#         index=True,
#     )

#     question: Mapped[str] = mapped_column(
#         Text,
#         nullable=False,
#     )

#     options: Mapped[list[str]] = mapped_column(
#         JSON,
#         nullable=False,
#     )

#     correct_option: Mapped[int] = mapped_column(
#         Integer,
#         nullable=False,
#     )

#     explanation: Mapped[str | None] = mapped_column(
#         Text,
#         nullable=True,
#     )

#     order: Mapped[int] = mapped_column(
#         Integer,
#         nullable=False,
#         default=0,
#     )

import uuid

from sqlalchemy import ForeignKey, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel


class QuizQuestion(BaseModel):
    __tablename__ = "quiz_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roadmap_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    options: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
    )

    correct_option: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    quiz: Mapped["Quiz"] = relationship(
        "Quiz",
        back_populates="questions",
    )