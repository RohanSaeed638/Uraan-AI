import asyncio
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException

from app.ai.schemas.learning_plan_schema import (
    LearningPlan,
    PlanUnit,
    READING_FLOOR_WORDS,
    READING_TARGET_WORDS,
    normalize_order,
    validate_plan,
    word_count,
)
from app.ai.services import learning_unit_generator as gen_module
from app.ai.services.learning_unit_generator import (
    LearningUnitGenerator,
    build_body_prompt,
    build_outline_prompt,
    strip_fence,
)
from app.ai.services.video_resolver import (
    is_search_url,
    resolve_video,
    search_url,
    youtube_id,
)
from app.services.task_learning_unit_service import TaskLearningUnitService

LONG = "word " * (READING_TARGET_WORDS + 20)
SHORT = "word " * 30
MEDIUM = "word " * (READING_FLOOR_WORDS + 10)  # above the floor, below target


def unit(day=1, order=1, type="reading", **extra):
    base = dict(
        day=day,
        order=order,
        type=type,
        title=f"{type} {day}.{order}",
        description="d",
        outline=["point one", "point two"] if type != "video" else [],
        estimated_minutes=30,
    )
    base.update(extra)
    return base


def plan(*units):
    return LearningPlan(units=list(units))


# ---- outline validation ---------------------------------------------------


def test_valid_reading_only_plan():
    validate_plan(plan(unit(1), unit(2)), "reading")


def test_rejects_video_for_reading_only_learner():
    with pytest.raises(ValueError, match="not allowed"):
        validate_plan(plan(unit(1), unit(1, 2, "video", search_query="q")), "reading")


def test_requires_a_reading():
    with pytest.raises(ValueError, match="reading"):
        validate_plan(
            plan(unit(1, 1, "video", search_query="q")), "reading_video"
        )


def test_days_must_start_at_one_without_gaps():
    with pytest.raises(ValueError, match="no gaps"):
        validate_plan(plan(unit(1), unit(3)), "reading")

    with pytest.raises(ValueError, match="no gaps"):
        validate_plan(plan(unit(2)), "reading")


def test_lessons_need_an_outline():
    with pytest.raises(ValueError, match="outline"):
        validate_plan(plan(unit(1, outline=["only one"])), "reading")


def test_video_needs_a_link_or_search_phrase():
    with pytest.raises(ValueError, match="no link"):
        validate_plan(plan(unit(1), unit(1, 2, "video")), "reading_video")


def test_at_most_one_project():
    with pytest.raises(ValueError, match="At most one"):
        validate_plan(
            plan(unit(1), unit(1, 2, "project"), unit(2, 1, "project")),
            "reading_video_project",
        )


def test_full_style_plan_is_valid():
    validate_plan(
        plan(
            unit(1),
            unit(1, 2, "video", search_query="q"),
            unit(2),
            unit(2, 2, "project"),
        ),
        "reading_video_project",
    )


def test_order_is_renumbered_per_day():
    ordered = normalize_order(plan(unit(2, 7), unit(1, 5), unit(1, 9)))

    assert [(u.day, u.order) for u in ordered] == [(1, 1), (1, 2), (2, 1)]


# ---- prompts --------------------------------------------------------------


def roadmap(style):
    return SimpleNamespace(
        career_slug="backend",
        skill_level=SimpleNamespace(value="beginner"),
        learning_goal="Get hired",
        daily_hours=2,
        learning_style=SimpleNamespace(value=style),
    )


TASK = SimpleNamespace(
    id=uuid4(),
    title="Learn HTTP",
    description="Understand requests",
    estimated_hours=4,
    resource_links=["https://developer.mozilla.org/en-US/docs/Web/HTTP"],
)


def test_outline_prompt_follows_learning_style():
    reading = build_outline_prompt(roadmap("reading"), TASK)
    video = build_outline_prompt(roadmap("reading_video"), TASK)
    full = build_outline_prompt(roadmap("reading_video_project"), TASK)

    assert "VIDEO lessons" not in reading and "PROJECT lesson" not in reading
    assert "VIDEO lessons" in video and "PROJECT lesson" not in video
    assert "VIDEO lessons" in full and "PROJECT lesson" in full
    assert "Learn HTTP" in full
    assert "Never invent URLs" in full


def test_body_prompt_lists_outline_and_other_lessons():
    units = normalize_order(plan(unit(1), unit(2, title="Second lesson")))
    first = units[0]

    prompt = build_body_prompt(first, units, roadmap("reading"), TASK)

    assert "- point one" in prompt
    assert "Day 2: Second lesson" in prompt
    assert f"{READING_TARGET_WORDS}+ words" in prompt
    assert "Key takeaways" in prompt and "Check yourself" in prompt


def test_project_body_prompt_uses_project_sections():
    units = normalize_order(plan(unit(1), unit(2, type="project")))

    prompt = build_body_prompt(units[1], units, roadmap("reading_video_project"), TASK)

    assert "What to submit" in prompt and "Stretch goal" in prompt


def test_strip_fence():
    assert strip_fence("```markdown\n## Hi\ntext\n```") == "## Hi\ntext"
    assert strip_fence("## Hi\n```py\ncode\n```\nend") == "## Hi\n```py\ncode\n```\nend"


# ---- video verification ---------------------------------------------------

GOOD = "dQw4w9WgXcQ"
BAD = "aaaaaaaaaaa"


def client(status_for):
    def handler(request: httpx.Request) -> httpx.Response:
        if "boom" in str(request.url):
            raise httpx.ConnectError("down")
        url = str(request.url)
        return httpx.Response(200 if status_for(url) else 404, json={})

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def test_youtube_id_forms():
    assert youtube_id(f"https://www.youtube.com/watch?v={GOOD}") == GOOD
    assert youtube_id(f"https://youtu.be/{GOOD}") == GOOD
    assert youtube_id(f"https://www.youtube.com/embed/{GOOD}") == GOOD
    assert youtube_id("https://example.com/video") is None
    assert youtube_id("") is None


def test_search_url_is_flagged_as_search():
    url = search_url("python decorators explained")

    assert is_search_url(url)
    assert "python+decorators+explained" in url
    assert not is_search_url(f"https://www.youtube.com/watch?v={GOOD}")


def test_first_existing_video_wins():
    async def run():
        async with client(lambda u: GOOD in u) as c:
            return await resolve_video(
                c,
                [f"https://www.youtube.com/watch?v={BAD}", f"https://youtu.be/{GOOD}"],
                "q",
                "fallback",
            )

    assert asyncio.run(run()) == f"https://www.youtube.com/watch?v={GOOD}"


def test_missing_videos_fall_back_to_search():
    async def run():
        async with client(lambda u: False) as c:
            return await resolve_video(
                c, [f"https://youtu.be/{BAD}", "not a url"], "my phrase", "fallback"
            )

    result = asyncio.run(run())

    assert is_search_url(result)
    assert "my+phrase" in result


def test_network_errors_fall_back_to_search():
    async def run():
        async with client(lambda u: True) as c:
            # "boom" in the video id makes the mock raise a connection error
            return await resolve_video(
                c, ["https://youtu.be/boomboomboo"], None, "fallback phrase"
            )

    result = asyncio.run(run())

    assert is_search_url(result)
    assert "fallback+phrase" in result


# ---- generator ------------------------------------------------------------


class Chat:
    """Scripted stand-in for the model: returns queued texts in order."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.prompts = []

    # Patched onto the class as an instance (not a function), so it is not
    # bound: `generator._chat(...)` calls this without the generator.
    async def __call__(self, prompt, system, max_tokens, json_mode):
        self.prompts.append(prompt)
        return self.answers.pop(0)


def outline_json(*units):
    return LearningPlan(units=list(units)).model_dump_json()


def patch_chat(monkeypatch, chat):
    monkeypatch.setattr(LearningUnitGenerator, "_chat", chat)


def test_generator_writes_each_lesson_and_resolves_videos(monkeypatch):
    outline = outline_json(
        unit(1),
        unit(1, 2, "video", video_urls=[f"https://youtu.be/{GOOD}"],
             search_query="q", notes="Watch for the verbs."),
        unit(2, 1, "project"),
    )
    # outline, then reading body, then project body (order of completion is
    # fixed here because lessons are written one after another in this test)
    chat = Chat(outline, LONG, LONG)
    patch_chat(monkeypatch, chat)

    async def fake_resolve(jobs):
        return [f"https://www.youtube.com/watch?v={GOOD}" for _ in jobs]

    monkeypatch.setattr(gen_module, "resolve_many", fake_resolve)
    monkeypatch.setattr(gen_module, "PARALLEL_WRITERS", 1)

    units = asyncio.run(
        LearningUnitGenerator().generate(roadmap("reading_video_project"), TASK)
    )

    assert [u["type"] for u in units] == ["reading", "video", "project"]
    assert units[0]["content"].split()[0] == "word"
    assert units[1]["resource_url"].endswith(GOOD)
    assert units[1]["content"] == "Watch for the verbs."
    assert units[0]["resource_url"] is None and units[2]["resource_url"] is None
    assert len(chat.prompts) == 3  # outline + 2 written lessons


def test_bad_outline_is_retried_once(monkeypatch):
    bad = outline_json(unit(1, outline=["only one"]))
    good = outline_json(unit(1))
    chat = Chat(bad, good, LONG)
    patch_chat(monkeypatch, chat)

    units = asyncio.run(LearningUnitGenerator().generate(roadmap("reading"), TASK))

    assert len(units) == 1
    assert len(chat.prompts) == 3  # bad outline, good outline, one lesson


def test_unusable_outline_twice_gives_up(monkeypatch):
    bad = outline_json(unit(1, outline=["only one"]))
    patch_chat(monkeypatch, Chat(bad, bad))

    with pytest.raises(ValueError, match="No usable lesson plan"):
        asyncio.run(LearningUnitGenerator().generate(roadmap("reading"), TASK))


def test_short_lesson_is_expanded_once(monkeypatch):
    chat = Chat(outline_json(unit(1)), SHORT, LONG)
    patch_chat(monkeypatch, chat)

    units = asyncio.run(LearningUnitGenerator().generate(roadmap("reading"), TASK))

    assert word_count(units[0]["content"]) >= READING_TARGET_WORDS
    assert "too short" in chat.prompts[-1]


def test_lesson_above_the_floor_is_accepted_after_expand(monkeypatch):
    chat = Chat(outline_json(unit(1)), SHORT, MEDIUM)
    patch_chat(monkeypatch, chat)

    units = asyncio.run(LearningUnitGenerator().generate(roadmap("reading"), TASK))

    assert word_count(units[0]["content"]) == word_count(MEDIUM)


def test_lesson_still_too_thin_is_rejected(monkeypatch):
    patch_chat(monkeypatch, Chat(outline_json(unit(1)), SHORT, SHORT))

    with pytest.raises(ValueError, match="too thin"):
        asyncio.run(LearningUnitGenerator().generate(roadmap("reading"), TASK))


# ---- service --------------------------------------------------------------


class _Db:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    async def execute(self, *args, **kwargs):
        return SimpleNamespace(scalar_one=lambda: roadmap("reading"))

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1


class _Profiles:
    async def get_by_auth_user_id(self, auth_user_id):
        return SimpleNamespace(id=uuid4())


class _Tasks:
    def __init__(self, task):
        self.task = task

    async def get_task_for_user(self, task_id, profile_id, fresh=False):
        return self.task


class _Units:
    def __init__(self, existing=None):
        self.existing = existing or []
        self.saved = []

    async def get_by_task_id(self, task_id):
        return self.existing

    async def create_many(self, units):
        self.saved = units
        return units


class _Generator:
    def __init__(self, fail=False):
        self.calls = 0
        self.fail = fail

    async def generate(self, roadmap, task):
        self.calls += 1
        if self.fail:
            raise ValueError("bad plan")
        return [
            dict(day=1, order=1, type="reading", title="T", description=None,
                 content=LONG, resource_url=None, estimated_minutes=30)
        ]


def make_task(units=()):
    return SimpleNamespace(
        id=uuid4(),
        learning_units=list(units),
        phase=SimpleNamespace(roadmap_id=uuid4()),
    )


def make_service(task, units=None, generator=None):
    service = TaskLearningUnitService.__new__(TaskLearningUnitService)
    service.db = _Db()
    service.profile_repository = _Profiles()
    service.task_repository = _Tasks(task)
    service.learning_unit_repository = units or _Units()
    service.generator = generator or _Generator()
    return service


def test_task_with_lessons_is_not_regenerated():
    task = make_task(units=[object()])
    generator = _Generator()
    service = make_service(task, generator=generator)

    result = asyncio.run(service.ensure_plan(task.id, uuid4()))

    assert result is task
    assert generator.calls == 0
    assert service.db.commits == 0


def test_empty_task_gets_lessons_saved():
    task = make_task()
    units, generator = _Units(), _Generator()
    service = make_service(task, units, generator)

    asyncio.run(service.ensure_plan(task.id, uuid4()))

    assert generator.calls == 1
    assert len(units.saved) == 1
    assert units.saved[0].task_id == task.id
    assert service.db.commits == 1


def test_lessons_written_while_waiting_are_reused():
    task = make_task()
    generator = _Generator()
    service = make_service(task, _Units(existing=[object()]), generator)

    asyncio.run(service.ensure_plan(task.id, uuid4()))

    assert generator.calls == 0
    assert service.db.commits == 0


def test_generation_failure_is_502_and_saves_nothing():
    task = make_task()
    units = _Units()
    service = make_service(task, units, _Generator(fail=True))

    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.ensure_plan(task.id, uuid4()))

    assert exc.value.status_code == 502
    assert units.saved == []
    assert service.db.commits == 0


def test_unknown_or_foreign_task_is_404():
    service = make_service(None)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.ensure_plan(uuid4(), uuid4()))

    assert exc.value.status_code == 404
