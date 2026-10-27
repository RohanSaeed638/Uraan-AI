from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ResourceItem(BaseModel):
    id: UUID
    title: str
    url: str
    type: str
    provider: str | None = None
    description: str | None = None
    is_free: bool
    difficulty: str | None = None
    career_slugs: list[str] = []

    # Everyone's average (None until someone rates it) and this learner's own
    # bookmark and rating.
    avg_rating: float | None = None
    rating_count: int = 0
    bookmarked: bool = False
    my_rating: int | None = None

    model_config = ConfigDict(from_attributes=True)


class ResourceListResponse(BaseModel):
    items: list[ResourceItem]
    total: int
    page: int
    page_size: int


class RatingRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
