"""What the mentor knows about a learner: facts for its prompt, and the
suggestion chips shown above the chat box. Everything here comes from the
database; none of it is AI-generated."""
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts.language import language_name
from app.models.profile import Profile
from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.task_learning_unit import TaskLearningUnit
from app.repositories.learning_repository import get_next_learning_unit
from app.repositories.roadmap_task_repository import RoadmapTaskRepository
from app.services.gamification_service import GamificationService

RECENT_LESSONS = 5

NO_CONTEXT = "LEARNER CONTEXT: nothing is known about this learner yet."


@dataclass
class Chip:
    id: str
    label: str
    # "ask": send `prompt` as the learner's message. "review": open the code
    # review panel.
    kind: str = "ask"
    prompt: str | None = None


@dataclass
class MentorContext:
    text: str = NO_CONTEXT
    chips: list[Chip] = field(default_factory=list)


def _value(item) -> str:
    return str(getattr(item, "value", item) or "").replace("_", " ")


def first_name(full_name: str | None) -> str:
    return (full_name or "").split(" ")[0] or "the learner"


def context_text(
    profile,
    *,
    summary: dict | None,
    next_unit=None,
    progress: dict | None = None,
    recent: list[str] | None = None,
) -> str:
    """The LEARNER CONTEXT block. `next_unit` is (roadmap, phase, task, unit)."""
    lines = [
        f"- Name: {first_name(profile.full_name)}",
        f"- Preferred language: {language_name(profile.language)}",
    ]

    if profile.career_slug:
        lines.append(f"- Career they are working towards: {profile.career_slug.replace('-', ' ')}")
    if profile.skill_level:
        lines.append(f"- Skill level: {_value(profile.skill_level)}")
    if profile.career_stage:
        lines.append(f"- Where they are now: {_value(profile.career_stage)}")
    if profile.learning_goal:
        lines.append(f"- Their goal: {profile.learning_goal}")

    lines.append(
        f"- Studies about {profile.daily_hours or 2} hour(s) a day; learning style: "
        f"{_value(profile.learning_style) or 'not set'}"
    )

    if next_unit is not None:
        roadmap, phase, task, unit = next_unit
        done = (progress or {}).get("completed", 0)
        total = (progress or {}).get("total", 0)

        lines.append(f"- Active roadmap: \"{roadmap.title}\" ({done} of {total} tasks done)")
        lines.append(f"- Current phase: \"{phase.title}\"; current task: \"{task.title}\"")
        lines.append(
            f"- Next lesson: \"{unit.title}\" ({_value(unit.type)}, day {unit.day}, "
            f"about {unit.estimated_minutes or 30} min)"
        )
    else:
        lines.append("- Active roadmap: none, or everything in it is finished.")

    if summary:
        lines.append(
            f"- Progress: level {summary['level']}, {summary['xp']} XP, "
            f"{summary['streak_days']}-day streak, {summary['weekly_xp']} XP this week"
        )

    if recent:
        lines.append("- Lessons finished recently: " + "; ".join(f"\"{t}\"" for t in recent))

    return "LEARNER CONTEXT (facts from their account):\n" + "\n".join(lines)


# Chip text shown to the learner, by language. The prompt a chip sends stays
# English: the mentor answers in the learner's language (see the system prompt).
CHIP_LABELS = {
    "en": {
        "explain": "Explain: {title}",
        "quiz": "Quiz me on {title}",
        "next": "What should I do next?",
        "start": "How do I get started?",
        "review": "Review my code",
        "interview": "Interview questions",
    },
    "ur": {
        "explain": "سمجھائیں: {title}",
        "quiz": "{title} پر میرا کوئز لیں",
        "next": "اب مجھے کیا کرنا چاہیے؟",
        "start": "میں شروع کیسے کروں؟",
        "review": "میرا کوڈ دیکھیں",
        "interview": "انٹرویو کے سوالات",
    },
    "ur-Latn": {
        "explain": "Samjhain: {title}",
        "quiz": "{title} par mera quiz lein",
        "next": "Ab mujhe kya karna chahiye?",
        "start": "Main shuru kaise karoon?",
        "review": "Mera code dekhein",
        "interview": "Interview ke sawalat",
    },
}


def chips_for(profile, next_unit=None) -> list[Chip]:
    chips: list[Chip] = []
    labels = CHIP_LABELS.get(getattr(profile, "language", None) or "en", CHIP_LABELS["en"])

    if next_unit is not None:
        _, _, task, unit = next_unit

        chips.append(
            Chip(
                "explain",
                labels["explain"].format(title=unit.title),
                prompt=f"Explain the lesson \"{unit.title}\" in simple terms, with one example.",
            )
        )
        chips.append(
            Chip(
                "quiz",
                labels["quiz"].format(title=task.title),
                prompt=(
                    f"Quiz me on \"{task.title}\". Ask one short question at a time and "
                    "wait for my answer before the next."
                ),
            )
        )
        chips.append(
            Chip(
                "next",
                labels["next"],
                prompt="Based on my roadmap and progress, what should I do next, and why?",
            )
        )
    else:
        chips.append(
            Chip(
                "start",
                labels["start"],
                prompt="I am just starting out. How should I begin, and how do I use Uraan AI?",
            )
        )

    chips.append(Chip("review", labels["review"], kind="review"))

    career = (profile.career_slug or "").replace("-", " ")
    chips.append(
        Chip(
            "interview",
            labels["interview"],
            prompt=(
                f"Give me 5 common interview questions for a {career or 'junior'} role. "
                "Then ask me the first one and wait for my answer."
            ),
        )
    )

    return chips


async def _recent_lessons(db: AsyncSession, profile: Profile) -> list[str]:
    rows = await db.execute(
        select(TaskLearningUnit.title)
        .join(RoadmapTask, RoadmapTask.id == TaskLearningUnit.task_id)
        .join(RoadmapPhase, RoadmapPhase.id == RoadmapTask.phase_id)
        .join(Roadmap, Roadmap.id == RoadmapPhase.roadmap_id)
        .where(
            Roadmap.profile_id == profile.id,
            TaskLearningUnit.completed.is_(True),
        )
        .order_by(TaskLearningUnit.updated_at.desc())
        .limit(RECENT_LESSONS)
    )

    return list(rows.scalars())


async def build_context(db: AsyncSession, profile: Profile) -> MentorContext:
    summary = await GamificationService(db).summary(profile)
    next_unit = await get_next_learning_unit(db, profile.auth_user_id)

    progress = None

    if next_unit is not None:
        progress = await RoadmapTaskRepository(db).get_roadmap_progress(next_unit[0].id)

    recent = await _recent_lessons(db, profile)

    return MentorContext(
        text=context_text(
            profile, summary=summary, next_unit=next_unit, progress=progress, recent=recent
        ),
        chips=chips_for(profile, next_unit),
    )
