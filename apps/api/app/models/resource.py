from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column, relationship
from app.models.base_model import BaseModel
from .enums import ResourceType
from enum import Enum
from sqlalchemy import Enum as SQLAlchemyEnum
class Resource(BaseModel):

    __tablename__ = "resources"

    # task_id = mapped_column(
    #     ForeignKey("roadmap_tasks.id")
    # )
    task_id = mapped_column(
        ForeignKey("roadmap_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = mapped_column(String(255))

    url = mapped_column(String(500))

    type = mapped_column(SQLAlchemyEnum(ResourceType))

    duration_minutes = mapped_column(
        Integer,
        nullable=True,
    )

    task = relationship(
        "RoadmapTask",
        back_populates="resources",
    )