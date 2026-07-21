from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import BaseModel


class Career(BaseModel):
    __tablename__ = "careers"

    name: Mapped[str] = mapped_column(String(200))

    slug: Mapped[str] = mapped_column(
        String(200),
        unique=True,
    )

    description: Mapped[str] = mapped_column(Text())

    icon: Mapped[str | None]

    category: Mapped[str | None]