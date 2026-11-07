"""Corrects the study time of lessons that were written before times followed
the content. A written reading lesson gets the time its text really takes, and
each task's estimated hours are set from its lessons. Videos, exercises and
projects keep their time. Run from apps/api:

    python scripts/recalculate_lesson_times.py          # shows what WOULD change, changes nothing
    python scripts/recalculate_lesson_times.py --yes    # really updates

Safe to run twice: the result depends only on the lesson text.
"""
import argparse
import asyncio
import selectors
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select, update  # noqa: E402

from app.ai.schemas.learning_plan_schema import estimate_reading_minutes  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.roadmap_task import RoadmapTask  # noqa: E402
from app.models.task_learning_unit import LearningUnitType, TaskLearningUnit  # noqa: E402
from app.services.lesson_writer import refresh_task_hours  # noqa: E402


async def main(really: bool) -> int:
    async with SessionLocal() as db:
        lessons = (
            await db.execute(
                select(TaskLearningUnit).where(
                    TaskLearningUnit.type == LearningUnitType.READING,
                    TaskLearningUnit.status == "ready",
                    TaskLearningUnit.content.is_not(None),
                )
            )
        ).scalars().all()

        changed, tasks = 0, set()

        for lesson in lessons:
            minutes = estimate_reading_minutes(lesson.content)

            if minutes != lesson.estimated_minutes:
                changed += 1
                tasks.add(lesson.task_id)

                if really:
                    await db.execute(
                        update(TaskLearningUnit).where(TaskLearningUnit.id == lesson.id).values(estimated_minutes=minutes)
                    )

        hours_changed = 0

        for task_id in tasks:
            if really:
                before = (await db.execute(select(RoadmapTask.estimated_hours).where(RoadmapTask.id == task_id))).scalar_one()
                after = await refresh_task_hours(db, task_id)
                hours_changed += before != after
            else:
                hours_changed += 1

        if really:
            await db.commit()

    verb = "Updated" if really else "Would update"
    print(f"{verb} {changed} of {len(lessons)} written reading lessons, across {len(tasks)} tasks "
          f"({hours_changed} with new estimated hours).")

    if not really:
        print("Nothing was changed. Run again with --yes to apply.")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--yes", action="store_true", help="really update (default: only show)")
    args = parser.parse_args()

    raise SystemExit(
        asyncio.run(main(args.yes), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
    )
