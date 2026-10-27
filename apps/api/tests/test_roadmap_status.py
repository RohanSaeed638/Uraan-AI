import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.models.enums import RoadmapStatus
from app.repositories.roadmap_repository import RoadmapRepository


class _Result:
    def __init__(self, row):
        self.row = row

    def scalars(self):
        return SimpleNamespace(first=lambda: self.row)


class _Db:
    def __init__(self, row):
        self.row = row

    async def execute(self, stmt):
        return _Result(self.row)


def _update(current, new):
    roadmap = SimpleNamespace(status=current)
    repo = RoadmapRepository(_Db(roadmap))

    asyncio.run(repo.update_status(uuid4(), new))

    return roadmap.status


def test_finishing_a_task_does_not_reactivate_an_archived_roadmap():
    assert _update(RoadmapStatus.ARCHIVED, RoadmapStatus.ACTIVE) is RoadmapStatus.ARCHIVED


def test_an_archived_roadmap_can_still_be_completed():
    assert _update(RoadmapStatus.ARCHIVED, RoadmapStatus.COMPLETED) is RoadmapStatus.COMPLETED


def test_a_completed_roadmap_returns_to_active_when_a_task_is_unchecked():
    assert _update(RoadmapStatus.COMPLETED, RoadmapStatus.ACTIVE) is RoadmapStatus.ACTIVE


def test_an_active_roadmap_becomes_completed():
    assert _update(RoadmapStatus.ACTIVE, RoadmapStatus.COMPLETED) is RoadmapStatus.COMPLETED


def test_a_new_roadmap_stores_the_request_it_was_made_from():
    """Lessons are written from these columns later, and they are NOT NULL."""
    from app.schemas.roadmap import RoadmapGenerateRequest

    request = RoadmapGenerateRequest(
        career_slug="video-editor", career_stage="beginner",
        skill_level="beginner", learning_goal="Become a Video Editor",
        daily_hours=2, target_duration=12, learning_style="reading",
    )

    fields = RoadmapRepository._request_fields(request)

    assert fields["career_slug"] == "video-editor"
    assert fields["learning_goal"] == "Become a Video Editor"
    assert fields["daily_hours"] == 2 and fields["target_duration"] == 12
    assert set(fields) == {
        "career_slug", "career_stage", "skill_level", "learning_goal",
        "learning_style", "daily_hours", "target_duration",
    }
    assert RoadmapRepository._request_fields(None) == {}


def test_ticking_a_task_does_not_unpause_a_paused_roadmap():
    assert _update(RoadmapStatus.PAUSED, RoadmapStatus.ACTIVE) is RoadmapStatus.PAUSED


def test_a_paused_roadmap_can_still_be_completed():
    assert _update(RoadmapStatus.PAUSED, RoadmapStatus.COMPLETED) is RoadmapStatus.COMPLETED


def test_a_roadmap_being_built_or_failed_is_left_alone():
    assert _update(RoadmapStatus.GENERATING, RoadmapStatus.ACTIVE) is RoadmapStatus.GENERATING
    assert _update(RoadmapStatus.GENERATING, RoadmapStatus.COMPLETED) is RoadmapStatus.GENERATING
    assert _update(RoadmapStatus.FAILED, RoadmapStatus.COMPLETED) is RoadmapStatus.FAILED
