import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.enums import LearningStyle, SkillLevel
from app.schemas.profile import (
    PatchProfileRequest,
    UpdateProfileRequest,
)
from app.services.profile_service import ProfileService


def test_onboarding_body_is_accepted():
    """Regression: the onboarding form omits career_stage and learning_goal
    and used to send upper-case learning styles, which the API rejected."""
    body = dict(
        full_name="A B",
        language="en",
        career_slug="backend-engineer",
        skill_level="beginner",
        learning_style="reading_video",
        daily_hours=2,
        target_duration=6,
        onboarding_completed=True,
    )

    request = UpdateProfileRequest(**body)

    assert request.learning_style is LearningStyle.READING_VIDEO
    assert request.career_stage is None and request.learning_goal is None


@pytest.mark.parametrize("style", ["READING", "Reading_Video", " reading_video_project "])
def test_learning_style_is_case_insensitive(style):
    assert PatchProfileRequest(learning_style=style).learning_style is not None


def test_patch_accepts_a_single_field():
    request = PatchProfileRequest(daily_hours=4)

    assert request.model_dump(exclude_unset=True) == {"daily_hours": 4}


def test_patch_cleans_text():
    request = PatchProfileRequest(
        full_name="  Rohan    Saeed ",
        country="  Pakistan ",
        learning_goal="   ",
        timezone="Asia/Karachi",
    )

    assert request.full_name == "Rohan Saeed"
    assert request.country == "Pakistan"
    assert request.learning_goal is None
    assert request.timezone == "Asia/Karachi"


@pytest.mark.parametrize(
    "bad",
    [
        {"full_name": "   "},
        {"full_name": "x" * 101},
        {"daily_hours": 0},
        {"daily_hours": 13},
        {"target_duration": 0},
        {"target_duration": 37},
        {"language": "klingon"},
        {"career_slug": "Not a career!"},
        {"timezone": "Mars/Olympus"},
        {"skill_level": "godlike"},
        {"learning_goal": "x" * 256},
        {"surprise": 1},
    ],
)
def test_patch_rejects_bad_values(bad):
    with pytest.raises(ValidationError):
        PatchProfileRequest(**bad)


class _Repo:
    def __init__(self, profile):
        self.profile = profile
        self.saved = 0

    async def get_by_auth_user_id(self, auth_user_id):
        return self.profile

    async def update(self, profile):
        self.saved += 1
        return profile

    async def career_exists(self, slug):
        return slug in {"backend-engineer", "data-analyst"}


def _profile():
    return SimpleNamespace(
        full_name="Old Name",
        language="en",
        country=None,
        timezone=None,
        career_slug="backend-engineer",
        skill_level=SkillLevel.BEGINNER,
        learning_style=LearningStyle.READING,
        career_stage=None,
        daily_hours=2,
        target_duration=6,
        learning_goal="Get hired",
    )


def test_patch_changes_only_the_fields_sent():
    profile = _profile()
    service = ProfileService(_Repo(profile))

    asyncio.run(
        service.patch_profile(
            uuid4(),
            PatchProfileRequest(
                full_name="New Name", daily_hours=5
            ).model_dump(exclude_unset=True),
        )
    )

    assert profile.full_name == "New Name"
    assert profile.daily_hours == 5
    # untouched
    assert profile.language == "en"
    assert profile.career_slug == "backend-engineer"
    assert profile.learning_goal == "Get hired"
    assert profile.target_duration == 6


def test_optional_fields_can_be_cleared():
    profile = _profile()
    service = ProfileService(_Repo(profile))

    asyncio.run(service.patch_profile(uuid4(), {"learning_goal": None}))

    assert profile.learning_goal is None


def test_required_fields_cannot_be_cleared():
    profile = _profile()
    repo = _Repo(profile)
    service = ProfileService(repo)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.patch_profile(uuid4(), {"career_slug": None}))

    assert exc.value.status_code == 422
    assert profile.career_slug == "backend-engineer"
    assert repo.saved == 0


def test_patching_a_missing_profile_is_404():
    service = ProfileService(_Repo(None))

    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.patch_profile(uuid4(), {"daily_hours": 3}))

    assert exc.value.status_code == 404


def test_an_unknown_career_is_refused_by_the_service():
    profile = _profile()
    repo = _Repo(profile)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(ProfileService(repo).patch_profile(uuid4(), {"career_slug": "wizard"}))

    assert exc.value.status_code == 422 and exc.value.detail == "Unknown career path"
    assert profile.career_slug == "backend-engineer" and repo.saved == 0


def test_a_career_in_the_database_is_accepted():
    profile = _profile()

    asyncio.run(ProfileService(_Repo(profile)).patch_profile(uuid4(), {"career_slug": "data-analyst"}))

    assert profile.career_slug == "data-analyst"
