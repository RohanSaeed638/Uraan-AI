# from sqlalchemy import (
#     String,
#     Text,
#     Integer,
#     ForeignKey,
# )
# from sqlalchemy.orm import Mapped, mapped_column, relationship

# from app.models.base_model import BaseModel


# class Quiz(BaseModel):
#     __tablename__ = "quizzes"

#     lesson_id: Mapped[str] = mapped_column(
#         ForeignKey("lessons.id", ondelete="CASCADE"),
#         nullable=False,
#         index=True,
#     )

#     title: Mapped[str] = mapped_column(
#         String(255),
#         nullable=False,
#     )

#     description: Mapped[str | None] = mapped_column(
#         Text,
#         nullable=True,
#     )

#     passing_score: Mapped[int] = mapped_column(
#         Integer,
#         nullable=False,
#         default=70,
#         server_default="70",
#     )

#     max_attempts: Mapped[int | None] = mapped_column(
#         Integer,
#         nullable=True,
#     )

#     questions = relationship(
#         "QuizQuestion",
#         back_populates="quiz",
#         cascade="all, delete-orphan",
#     )


# from sqlalchemy import String, Text, Integer, ForeignKey
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.orm import Mapped, mapped_column, relationship

# from app.models.base_model import BaseModel


# class Quiz(BaseModel):
#     __tablename__ = "quizzes"

#     lesson_id: Mapped[str] = mapped_column(
#         ForeignKey("lessons.id", ondelete="CASCADE"),
#         nullable=False,
#         index=True,
#     )

#     title: Mapped[str] = mapped_column(
#         String(255),
#         nullable=False,
#     )

#     description: Mapped[str | None] = mapped_column(
#         Text,
#         nullable=True,
#     )

#     passing_score: Mapped[int] = mapped_column(
#         Integer,
#         nullable=False,
#         default=70,
#         server_default="70",
#     )

#     max_attempts: Mapped[int | None] = mapped_column(
#         Integer,
#         nullable=True,
#     )

#     questions: Mapped[list["QuizQuestion"]] = relationship(
#         "QuizQuestion",
#         back_populates="quiz",
#         cascade="all, delete-orphan",
#         order_by="QuizQuestion.order",
#     )

import uuid

from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel


class Quiz(BaseModel):
    __tablename__ = "quizzes"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roadmap_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    passing_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=70,
        server_default="70",
    )

    max_attempts: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    questions: Mapped[list["QuizQuestion"]] = relationship(
        "QuizQuestion",
        back_populates="quiz",
        cascade="all, delete-orphan",
        order_by="QuizQuestion.order",
    )