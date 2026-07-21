from app.db.mixins import UUIDMixin
from app.db.mixins import TimestampMixin

from app.db.session import Base


class BaseModel(
    Base,
    UUIDMixin,
    TimestampMixin,
):
    __abstract__ = True