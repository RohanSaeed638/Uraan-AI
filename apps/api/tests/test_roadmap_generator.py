"""The roadmap AI: what the prompt carries, and that unusable replies are never saved."""
import asyncio
import json
import selectors
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.ai.services import roadmap_generator
from app.ai.services.roadmap_generator import RoadmapGenerator, _bullets, _value
from app.models.enums import CareerStage, LearningStyle, SkillLevel


def run(coro):
    return asyncio.run(coro, loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


PLAN = {
    "title": "Backend Engineer in 6 months",
    "description": "From zero to your first job.",
    "phases": [
        {
            "title": "Foundations", "description": "Basics", "order": 1, "estimated_weeks": 4,
            "milestones": ["Write a script"],
            "tasks": [
                {"title": "Learn Python", "description": "Syntax", "resource_links": ["https://python.org"],
                 "difficulty": "easy", "estimated_hours": 10, "week": 1},
            ],
        }
    ],
}


class FakeAI:
    def __init__(self, reply):
        self.reply, self.calls = reply, []

    async def __call__(self, messages, **options):
        self.calls.append({"messages": messages, **options})
        return self.reply if isinstance(self.reply, str) else json.dumps(self.reply)


def use(monkeypatch, reply=PLAN):
    fake = FakeAI(reply)
    monkeypatch.setattr(roadmap_generator, "complete_text", fake)
    return fake


profile = SimpleNamespace(
    full_name="Sana Khan", device="mobile", education=None, goal_type=None, learning_pace=None,
    preferred_study_hours=None, weekend_study=None, age=None, language="en",
)
request = SimpleNamespace(
    career_slug="backend-engineer", career_stage=CareerStage.BEGINNER, skill_level=SkillLevel.BEGINNER,
    learning_goal="get my first job", learning_style=LearningStyle.READING, daily_hours=2, target_duration=6,
)


def test_a_whole_roadmap_is_requested_from_what_the_learner_asked_for(monkeypatch):
    fake = use(monkeypatch)
    result = run(RoadmapGenerator().generate(profile, request))

    prompt = fake.calls[0]["messages"][1]["content"]
    assert result.title == "Backend Engineer in 6 months" and result.phases[0].tasks[0].week == 1
    for fact in ("Sana Khan", "backend-engineer", "get my first job"):
        assert fact in prompt

    assert "CareerStage" not in prompt and "SkillLevel" not in prompt  # plain words, not enum names
    assert "mobile phone" in prompt  # the learner's device shapes the plan


def test_the_request_goes_out_as_a_json_roadmap_job(monkeypatch):
    fake = use(monkeypatch)
    run(RoadmapGenerator().generate(profile, request))

    sent = fake.calls[0]
    assert sent["purpose"] == "roadmap" and sent["json_mode"] is True and sent["max_tokens"] >= 4000


def test_the_catalogues_curated_template_is_included_when_there_is_one(monkeypatch):
    fake = use(monkeypatch)
    career = SimpleNamespace(
        name="Backend Engineer", estimated_months=6,
        skills=[SimpleNamespace(name="HTTP", order_number=2), SimpleNamespace(name="Python", order_number=1)],
        resources=[SimpleNamespace(title="CS50", provider="Harvard", type="course", url="https://cs50.harvard.edu", order_number=1)],
    )
    run(RoadmapGenerator().generate(profile, request, career=career))
    prompt = fake.calls[0]["messages"][1]["content"]

    assert "1. Python" in prompt and "2. HTTP" in prompt and "https://cs50.harvard.edu" in prompt


@pytest.mark.parametrize(
    "bad",
    [
        {"title": "No phases", "description": "d"},
        {**PLAN, "phases": [{**PLAN["phases"][0], "tasks": [{"title": "t"}]}]},
        {**PLAN, "title": None},
    ],
)
def test_a_reply_that_does_not_fit_the_shape_is_rejected(monkeypatch, bad):
    use(monkeypatch, bad)

    with pytest.raises(ValidationError):
        run(RoadmapGenerator().generate(profile, request))


def test_a_reply_wrapped_in_a_code_fence_is_understood(monkeypatch):
    use(monkeypatch, "```json\n" + json.dumps(PLAN) + "\n```")

    assert run(RoadmapGenerator().generate(profile, request)).phases[0].title == "Foundations"


def test_an_unparseable_reply_fails_loudly_so_the_job_can_report_it(monkeypatch):
    use(monkeypatch, "I cannot help with that.")

    with pytest.raises(json.JSONDecodeError):
        run(RoadmapGenerator().generate(profile, request))


# ---- adapting ------------------------------------------------------------------------------------------------------------------


stored = SimpleNamespace(
    career_slug="backend-engineer", career_stage="beginner", skill_level=SkillLevel.BEGINNER,
    learning_goal="job", learning_style=LearningStyle.READING,
)


def adapt(monkeypatch, **over):
    fake = use(monkeypatch)
    args = dict(completed=["Learn Python"], unfinished=["Learn HTTP", "Learn SQL"], daily_hours=1, months_left=3, reason="behind")
    args.update(over)
    run(RoadmapGenerator().adapt(profile, stored, **args))
    return fake.calls[0]


def test_adapting_lists_what_is_done_and_what_is_left(monkeypatch):
    call = adapt(monkeypatch)
    prompt = call["messages"][1]["content"]

    assert "- Learn Python" in prompt and "- Learn HTTP" in prompt and "- Learn SQL" in prompt
    assert call["purpose"] == "roadmap_adapt"


def test_the_reason_and_the_learners_own_words_are_in_the_prompt(monkeypatch):
    prompt = adapt(monkeypatch, reason="study_time", note="I now work evenings")["messages"][1]["content"]

    assert "study time changed" in prompt and "I now work evenings" in prompt


def test_the_time_left_is_given_in_months_and_weeks(monkeypatch):
    prompt = adapt(monkeypatch, months_left=3)["messages"][1]["content"]

    assert "3" in prompt and "12" in prompt


def test_nothing_completed_is_written_as_nothing_not_left_blank(monkeypatch):
    prompt = adapt(monkeypatch, completed=[])["messages"][1]["content"]

    assert "- (nothing)" in prompt


def test_an_unknown_reason_is_refused_before_the_ai_is_called(monkeypatch):
    fake = use(monkeypatch)

    with pytest.raises(KeyError):
        run(RoadmapGenerator().adapt(profile, stored, completed=[], unfinished=["x"], daily_hours=1, months_left=1, reason="bored"))

    assert fake.calls == []


# ---- helpers --------------------------------------------------------------------------------------------------------------------


def test_enums_are_written_as_their_plain_value():
    assert _value(CareerStage.BEGINNER) == "beginner"
    assert _value("already text") == "already text"
    assert _value(5) == "5"


def test_bullets():
    assert _bullets(["a", "b"]) == "- a\n- b"
    assert _bullets([]) == "- (nothing)"
