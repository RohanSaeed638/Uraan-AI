import re
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,38}[a-z0-9])$")
RESERVED_SLUGS = {"admin", "api", "login", "register", "settings", "p"}

CHECKLIST = [
    ("readme", "Every project has a README with what it does and how to run it"),
    ("pinned", "Your best 3 to 6 repositories are pinned on your GitHub profile"),
    ("photo", "Your GitHub profile has a photo and a short bio"),
    ("commits", "You commit regularly with clear messages"),
    ("secrets", "No secrets or keys in your repositories, and a .gitignore is set"),
    ("live", "At least one project is deployed with a live demo link"),
]
CHECKLIST_IDS = {item_id for item_id, _ in CHECKLIST}


def _clean_url(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip()

    if not value:
        return None

    if not re.match(r"^https?://[^\s]+$", value, re.IGNORECASE):
        raise ValueError("Links must start with http:// or https://")

    return value


class ProjectFields(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    repo_url: str | None = Field(default=None, max_length=300)
    live_url: str | None = Field(default=None, max_length=300)
    tech: list[str] | None = Field(default=None, max_length=15)
    visible: bool | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("repo_url", "live_url")
    @classmethod
    def validate_url(cls, value):
        return _clean_url(value)

    @field_validator("tech")
    @classmethod
    def validate_tech(cls, value):
        if value is None:
            return value

        cleaned = [t.strip() for t in value if t and t.strip()]

        if any(len(t) > 40 for t in cleaned):
            raise ValueError("Each technology must be 40 characters or fewer")

        return list(dict.fromkeys(cleaned))


class CreateProjectRequest(ProjectFields):
    # Create from a completed roadmap project lesson; title, description
    # and so on then default from the lesson.
    source_unit_id: UUID | None = None


class UpdatePortfolioRequest(BaseModel):
    headline: str | None = Field(default=None, max_length=160)
    bio: str | None = Field(default=None, max_length=2000)
    slug: str | None = None
    is_public: bool | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value):
        if value is None:
            return value

        value = value.strip().lower()

        if not SLUG_RE.match(value):
            raise ValueError(
                "Use 3 to 40 lowercase letters, numbers or hyphens"
            )

        if value in RESERVED_SLUGS:
            raise ValueError("That address is reserved")

        return value


class ChecklistUpdateRequest(BaseModel):
    item_id: str
    done: bool

    model_config = ConfigDict(extra="forbid")

    @field_validator("item_id")
    @classmethod
    def known_item(cls, value):
        if value not in CHECKLIST_IDS:
            raise ValueError("Unknown checklist item")
        return value


class ProjectResponse(BaseModel):
    id: UUID
    source_unit_id: UUID | None = None
    title: str
    description: str | None = None
    repo_url: str | None = None
    live_url: str | None = None
    tech: list[str]
    visible: bool

    model_config = ConfigDict(from_attributes=True)


class ChecklistItem(BaseModel):
    id: str
    label: str
    done: bool


class Suggestion(BaseModel):
    unit_id: UUID
    title: str
    task_title: str


class PortfolioResponse(BaseModel):
    headline: str | None = None
    bio: str | None = None
    slug: str | None = None
    is_public: bool
    projects: list[ProjectResponse]
    checklist: list[ChecklistItem]
    suggestions: list[Suggestion]


class PublicProject(BaseModel):
    title: str
    description: str | None = None
    repo_url: str | None = None
    live_url: str | None = None
    tech: list[str]

    model_config = ConfigDict(from_attributes=True)


class PublicPortfolioResponse(BaseModel):
    name: str
    headline: str | None = None
    bio: str | None = None
    projects: list[PublicProject]


class DraftDescriptionResponse(BaseModel):
    description: str
