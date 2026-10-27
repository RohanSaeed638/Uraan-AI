from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.ai.prompts.learner_context import learner_context
from app.schemas.profile import PatchProfileRequest, UpdateProfileRequest

BASE = {
    "full_name": "Ayesha Khan",
    "language": "en",
    "career_slug": "backend-engineer",
    "skill_level": "beginner",
    "daily_hours": 2,
    "target_duration": 6,
    "learning_style": "reading",
    "onboarding_completed": True,
}


def profile(**kw):
    base = dict(
        age=None, education=None, device=None, goal_type=None,
        learning_pace=None, weekend_study=None,
    )
    return SimpleNamespace(**{**base, **kw})


def test_onboarding_accepts_new_fields_case_insensitively():
    data = UpdateProfileRequest(
        **BASE, age=19, education="BACHELORS", device="Mobile",
        goal_type="remote_job", preferred_study_hours="Evening",
        learning_pace="steady", weekend_study=False,
    )

    assert data.device == "mobile"
    assert data.preferred_study_hours == "evening"
    assert data.weekend_study is False


def test_new_fields_are_optional_in_onboarding():
    assert UpdateProfileRequest(**BASE).device is None


@pytest.mark.parametrize(
    "field, value",
    [("age", 5), ("age", 150), ("device", "tablet"), ("goal_type", "rich"),
     ("education", "phd"), ("learning_pace", "insane")],
)
def test_invalid_values_rejected(field, value):
    with pytest.raises(ValidationError):
        PatchProfileRequest(**{field: value})


def test_patch_only_carries_what_was_sent():
    changes = PatchProfileRequest(device="laptop").model_dump(exclude_unset=True)

    assert changes == {"device": "laptop"}


def test_mobile_only_learner_gets_no_install_tasks():
    text = learner_context(profile(device="mobile"))

    assert "only has a mobile phone" in text
    assert "Do NOT require installing" in text


def test_context_covers_goal_pace_and_weekends():
    text = learner_context(profile(
        age=20, education="college", goal_type="freelancing",
        learning_pace="intensive", weekend_study=False,
    ))

    assert "is 20 years old and is in college" in text
    assert "freelancing" in text
    assert "intensive" in text
    assert "weekdays only" in text


def test_no_answers_means_no_extra_prompt_text():
    assert learner_context(profile()) == ""
    assert learner_context(None) == ""


def test_real_db_profile_saves_every_career_stage():
    """career_stage once crashed on save: the model wrote 'BEGINNER' into a
    database type that holds 'beginner'."""
    import asyncio
    import selectors
    from uuid import uuid4

    from sqlalchemy import select, text
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

    from app.models.enums import CareerStage
    from app.models.profile import Profile

    async def run():
        from app.core.config import settings

        engine = create_async_engine(settings.DATABASE_URL)
        try:
            async with engine.connect() as conn:
                trans = await conn.begin()
                db = AsyncSession(bind=conn, join_transaction_mode="create_savepoint")
                try:
                    for stage in CareerStage:
                        profile = Profile(
                            auth_user_id=uuid4(), full_name="T", career_stage=stage,
                        )
                        db.add(profile)
                        await db.flush()
                        await db.refresh(profile)
                        assert profile.career_stage is stage

                    raw = (
                        await db.execute(
                            text("select distinct career_stage::text from profiles")
                        )
                    ).scalars().all()
                    assert set(raw) >= {s.value for s in CareerStage}
                finally:
                    await db.close()
                    await trans.rollback()
        finally:
            await engine.dispose()

    try:
        asyncio.run(
            run(),
            loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()),
        )
    except OSError as exc:
        pytest.skip(f"database not reachable: {type(exc).__name__}")
