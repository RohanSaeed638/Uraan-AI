"""Coding exercises and project details in generated lessons."""
import asyncio
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.ai.prompts.learning_units_prompt import rules_for
from app.ai.schemas.exercise_schema import ExerciseOutput
from app.ai.schemas.learning_plan_schema import (
    LearningPlan,
    READING_TARGET_WORDS,
    allowed_types,
    validate_plan,
)
from app.ai.services.learning_unit_generator import (
    LearningUnitGenerator,
    build_outline_prompt,
    project_details,
)
from app.core.career_catalog import is_coding_career
from app.ai.schemas.learning_plan_schema import PlanUnit

LONG = "word " * (READING_TARGET_WORDS + 20)
PROBLEM = (
    "Write a function `total(prices)` that returns the sum of a list of prices. "
    "For example total([2, 3, 5]) returns 10. An empty list gives 0. Do not use "
    "the built in sum function."
)


def unit(day=1, order=1, type="reading", **extra):
    base = dict(
        day=day, order=order, type=type, title=f"{type} {day}.{order}",
        description="d",
        outline=["point one", "point two"] if type != "video" else [],
        estimated_minutes=20,
    )
    if type == "exercise":
        base["language"] = "python"
    base.update(extra)
    return base


def plan(*units):
    return LearningPlan(units=list(units))


def exercise(**over):
    data = dict(
        language="python",
        problem=PROBLEM,
        starter_code="def total(prices):\n    # TODO\n    pass\n",
        hints=["Start with a variable for the running total.", "Loop over the list."],
        solution="def total(prices):\n    result = 0\n    for p in prices:\n        result += p\n    return result\n",
        expected_output="10",
    )
    data.update(over)
    return ExerciseOutput(**data)


# ---- which careers get exercises ----------------------------------------------------


def test_only_coding_careers_get_exercises():
    assert is_coding_career("backend-engineer")
    assert is_coding_career("data-scientist")
    assert is_coding_career("cyber-security")
    assert not is_coding_career("video-editor")
    assert not is_coding_career("digital-marketer")
    assert not is_coding_career("not-a-career")
    assert not is_coding_career(None)


def test_exercises_join_every_learning_style_for_coding_careers():
    assert "exercise" not in allowed_types("reading")
    assert "exercise" in allowed_types("reading", coding=True)
    assert allowed_types("reading_video_project", coding=True) == {
        "reading", "video", "project", "exercise",
    }


def test_outline_prompt_only_mentions_exercises_for_coding_careers():
    roadmap = SimpleNamespace(
        career_slug="backend-engineer", skill_level=SimpleNamespace(value="beginner"),
        learning_goal="job", daily_hours=2, learning_style=SimpleNamespace(value="reading"),
    )
    task = SimpleNamespace(title="HTTP", description="d", estimated_hours=3, resource_links=[])

    assert "EXERCISE lessons" in build_outline_prompt(roadmap, task, None, True)
    assert "EXERCISE lessons" not in build_outline_prompt(roadmap, task, None, False)
    assert "EXERCISE" not in rules_for("reading")


# ---- plan validation -------------------------------------------------------------------


def test_exercise_plan_valid_for_coding_but_not_otherwise():
    p = plan(unit(1), unit(2, 1, "exercise"))

    validate_plan(p, "reading", coding=True)

    with pytest.raises(ValueError, match="not allowed"):
        validate_plan(p, "reading", coding=False)


def test_at_most_one_exercise_a_day_and_three_a_task():
    two_in_a_day = plan(unit(1), unit(1, 2, "exercise"), unit(1, 3, "exercise"))

    with pytest.raises(ValueError, match="one exercise per day"):
        validate_plan(two_in_a_day, "reading", coding=True)

    four = plan(unit(1), *[unit(d, 1, "exercise") for d in (2, 3, 4, 5)])

    with pytest.raises(ValueError, match="At most 3 exercises"):
        validate_plan(four, "reading", coding=True)


def test_an_exercise_needs_a_language_and_an_outline():
    no_language = plan(unit(1), unit(2, 1, "exercise", language=None))

    with pytest.raises(ValueError, match="needs a language"):
        validate_plan(no_language, "reading", coding=True)

    thin = plan(unit(1), unit(2, 1, "exercise", outline=["only one"]))

    with pytest.raises(ValueError, match="outline"):
        validate_plan(thin, "reading", coding=True)


# ---- exercise checks ---------------------------------------------------------------------


def test_a_good_exercise_passes():
    exercise().check()


def test_python_that_does_not_parse_is_rejected():
    with pytest.raises(ValueError, match="solution is not valid Python"):
        exercise(solution="def total(prices:\n    return 1").check()

    with pytest.raises(ValueError, match="starter code is not valid Python"):
        exercise(starter_code="def (").check()


def test_other_languages_are_not_parsed():
    exercise(
        language="javascript",
        starter_code="function total(prices) { /* TODO */ }",
        solution="function total(prices) { return prices.reduce((a, b) => a + b, 0); }",
    ).check()


@pytest.mark.parametrize(
    "over, match",
    [
        ({"problem": "Too short."}, "too short"),
        ({"starter_code": "x = 1", "solution": "x = 1"}, "already is the solution"),
    ],
)
def test_unusable_exercises_are_rejected(over, match):
    with pytest.raises(ValueError, match=match):
        exercise(**over).check()


def test_structure_errors_are_caught_on_creation():
    with pytest.raises(ValidationError):
        exercise(hints=["only one"])

    with pytest.raises(ValidationError):
        exercise(solution="   ")


def test_details_carry_what_the_page_needs():
    details = exercise().as_details()

    assert set(details) == {"language", "starter_code", "hints", "solution", "expected_output"}
    assert details["language"] == "python"


# ---- project details ------------------------------------------------------------------------


def test_project_details_are_tidied():
    u = PlanUnit(
        day=1, type="project", title="t", outline=["a", "b"], estimated_minutes=30,
        difficulty=" Intermediate ", skills=["APIs", " APIs ", "", "SQL"],
        portfolio_value="  Shows you can ship.  ",
    )

    assert project_details(u) == {
        "difficulty": "intermediate", "skills": ["APIs", "SQL"],
        "portfolio_value": "Shows you can ship.",
    }


def test_unknown_difficulty_is_dropped():
    u = PlanUnit(day=1, type="project", title="t", outline=["a", "b"],
                 estimated_minutes=30, difficulty="insane")

    assert project_details(u)["difficulty"] is None


# ---- the generator ---------------------------------------------------------------------------


class Chat:
    def __init__(self, *answers):
        self.answers, self.prompts = list(answers), []

    async def __call__(self, prompt, system, max_tokens, json_mode):
        self.prompts.append(prompt)
        return self.answers.pop(0)


def coding_roadmap(style="reading_video_project", slug="backend-engineer"):
    return SimpleNamespace(
        career_slug=slug, skill_level=SimpleNamespace(value="beginner"),
        learning_goal="job", daily_hours=2, learning_style=SimpleNamespace(value=style),
    )


TASK = SimpleNamespace(
    id=uuid4(), title="Python functions", description="d", estimated_hours=4, resource_links=[],
)


def exercise_json(**over):
    data = dict(
        language="python", problem=PROBLEM,
        starter_code="def total(prices):\n    pass\n",
        hints=["h1", "h2"],
        solution="def total(prices):\n    return sum(prices)\n",
        expected_output="10",
    )
    data.update(over)
    return json.dumps(data)


def test_generator_stores_exercise_and_project_details(monkeypatch):
    outline = plan(
        unit(1),
        unit(2, 1, "exercise"),
        unit(3, 1, "project", difficulty="beginner", skills=["Functions"], portfolio_value="Shows basics."),
    ).model_dump_json()
    chat = Chat(outline, LONG, exercise_json(), LONG)
    monkeypatch.setattr(LearningUnitGenerator, "_chat", chat)
    from app.ai.services import learning_unit_generator as gen_module
    monkeypatch.setattr(gen_module, "PARALLEL_WRITERS", 1)

    units = asyncio.run(LearningUnitGenerator().generate(coding_roadmap(), TASK))

    assert [u["type"] for u in units] == ["reading", "exercise", "project"]

    ex = units[1]
    assert ex["content"].startswith("Write a function")
    assert ex["details"]["starter_code"].startswith("def total")
    assert ex["details"]["hints"] == ["h1", "h2"]
    assert "sum(prices)" in ex["details"]["solution"]

    assert units[0]["details"] is None
    assert units[2]["details"] == {
        "difficulty": "beginner", "skills": ["Functions"], "portfolio_value": "Shows basics.",
    }


def test_a_broken_exercise_is_asked_for_again_once(monkeypatch):
    bad = exercise_json(solution="def total(:")
    chat = Chat(plan(unit(1), unit(2, 1, "exercise")).model_dump_json(), LONG, bad, exercise_json())
    monkeypatch.setattr(LearningUnitGenerator, "_chat", chat)
    from app.ai.services import learning_unit_generator as gen_module
    monkeypatch.setattr(gen_module, "PARALLEL_WRITERS", 1)

    units = asyncio.run(LearningUnitGenerator().generate(coding_roadmap("reading"), TASK))

    assert units[1]["details"]["language"] == "python"
    assert len(chat.prompts) == 4


def test_an_exercise_that_stays_broken_fails_the_plan(monkeypatch):
    bad = exercise_json(solution="def total(:")
    chat = Chat(plan(unit(1), unit(2, 1, "exercise")).model_dump_json(), LONG, bad, bad)
    monkeypatch.setattr(LearningUnitGenerator, "_chat", chat)
    from app.ai.services import learning_unit_generator as gen_module
    monkeypatch.setattr(gen_module, "PARALLEL_WRITERS", 1)

    with pytest.raises(ValueError, match="could not be written"):
        asyncio.run(LearningUnitGenerator().generate(coding_roadmap("reading"), TASK))


def test_non_coding_careers_cannot_get_exercises(monkeypatch):
    outline = plan(unit(1), unit(2, 1, "exercise")).model_dump_json()
    chat = Chat(outline, outline)
    monkeypatch.setattr(LearningUnitGenerator, "_chat", chat)

    with pytest.raises(ValueError, match="No usable lesson plan"):
        asyncio.run(
            LearningUnitGenerator().generate(coding_roadmap("reading", "video-editor"), TASK)
        )


# ---- trimming a plan with too many exercises ----------------------------------------------------


def test_surplus_exercises_are_dropped_not_fatal():
    from app.ai.schemas.learning_plan_schema import trim_exercises

    p = plan(
        unit(1), unit(1, 2, "exercise"), unit(1, 3, "exercise"),  # two on day 1
        unit(2), unit(2, 2, "exercise"),
        unit(3), unit(3, 2, "exercise"),
        unit(4), unit(4, 2, "exercise"),                          # a fourth in total
    )

    trim_exercises(p)

    assert [u.type for u in p.units].count("exercise") == 3
    validate_plan(p, "reading", coding=True)  # and the result is valid


def test_days_are_closed_up_after_trimming():
    from app.ai.schemas.learning_plan_schema import trim_exercises

    # day 3 holds only a surplus exercise: it disappears and day 4 becomes 3
    p = plan(
        unit(1, 1, "exercise"), unit(1, 2), unit(2, 1, "exercise"), unit(2, 2),
        unit(3, 1, "exercise"), unit(3, 2), unit(4, 1, "exercise"),
    )
    p.units[-1].title = "surplus"

    trim_exercises(p)

    assert sorted({u.day for u in p.units}) == [1, 2, 3]
    assert "surplus" not in [u.title for u in p.units]


def test_trimming_leaves_a_valid_plan_alone():
    from app.ai.schemas.learning_plan_schema import trim_exercises

    p = plan(unit(1), unit(2, 1, "exercise"), unit(3))
    before = [(u.day, u.order, u.type) for u in p.units]

    trim_exercises(p)

    assert [(u.day, u.order, u.type) for u in p.units] == before


def test_generator_trims_an_overeager_outline(monkeypatch):
    p = plan(
        unit(1), unit(1, 2, "exercise"), unit(2, 1, "exercise"),
        unit(3, 1, "exercise"), unit(4, 1, "exercise"),
    )
    answers = [p.model_dump_json()] + [LONG] + [exercise_json()] * 3
    chat = Chat(*answers)
    monkeypatch.setattr(LearningUnitGenerator, "_chat", chat)
    from app.ai.services import learning_unit_generator as gen_module
    monkeypatch.setattr(gen_module, "PARALLEL_WRITERS", 1)

    units = asyncio.run(LearningUnitGenerator().generate(coding_roadmap("reading"), TASK))

    assert [u["type"] for u in units].count("exercise") == 3
