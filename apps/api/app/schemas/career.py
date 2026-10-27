from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CareerSkillResponse(BaseModel):
    name: str
    order_number: int

    model_config = ConfigDict(from_attributes=True)


class CareerResourceResponse(BaseModel):
    title: str
    type: str
    provider: str | None = None
    url: str
    is_free: bool
    difficulty: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CareerSummary(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str
    category: str | None = None
    icon: str | None = None
    color: str | None = None
    difficulty: str | None = None
    estimated_months: int | None = None
    salary_min_pkr: int | None = None
    salary_max_pkr: int | None = None
    market_demand: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CareerDetail(CareerSummary):
    skills: list[CareerSkillResponse] = []
    resources: list[CareerResourceResponse] = []


class CareerListResponse(BaseModel):
    items: list[CareerSummary]
    total: int
    page: int
    page_size: int


class CompareRequest(BaseModel):
    slugs: list[str] = Field(min_length=2, max_length=4)


class CompareResponse(BaseModel):
    careers: list[CareerDetail]


class RecommendRequest(BaseModel):
    """What the learner tells us. Anything left out comes from their profile."""

    interests: str = Field(min_length=3, max_length=500)
    experience: str | None = Field(default=None, max_length=300)
    education: str | None = Field(default=None, max_length=60)
    daily_hours: int | None = Field(default=None, ge=1, le=12)
    goal: str | None = Field(default=None, max_length=255)


class Recommendation(BaseModel):
    career: CareerSummary
    reason: str


class RecommendResponse(BaseModel):
    recommendations: list[Recommendation]
