"""Learners say whether a lesson helped, and why when it did not."""
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import LessonFeedback
from app.models.roadmap import Roadmap
from app.models.roadmap_phase import RoadmapPhase
from app.models.roadmap_task import RoadmapTask
from app.models.task_learning_unit import TaskLearningUnit
from app.repositories.profile_repository import ProfileRepository
from app.schemas.feedback import FeedbackRequest, FeedbackResponse


def _out(row: LessonFeedback | None) -> FeedbackResponse | None:
    if row is None:
        return None

    return FeedbackResponse(helpful=row.helpful, reason=row.reason, comment=row.comment)


class FeedbackService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.profiles = ProfileRepository(db)

    async def _profile(self, auth_user_id: UUID):
        profile = await self.profiles.get_by_auth_user_id(auth_user_id)

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        return profile

    async def _lesson(self, unit_id: UUID, profile_id: UUID):
        """The lesson with its task title and career, only if it is the learner's own."""
        row = (
            await self.db.execute(
                select(TaskLearningUnit, RoadmapTask.title, Roadmap.career_slug)
                .join(RoadmapTask, RoadmapTask.id == TaskLearningUnit.task_id)
                .join(RoadmapPhase, RoadmapPhase.id == RoadmapTask.phase_id)
                .join(Roadmap, Roadmap.id == RoadmapPhase.roadmap_id)
                .where(TaskLearningUnit.id == unit_id, Roadmap.profile_id == profile_id)
            )
        ).first()

        if row is None:
            raise HTTPException(status_code=404, detail="Learning unit not found")

        return row

    async def get(self, unit_id: UUID, auth_user_id: UUID) -> FeedbackResponse | None:
        profile = await self._profile(auth_user_id)
        await self._lesson(unit_id, profile.id)

        return _out(
            (
                await self.db.execute(
                    select(LessonFeedback).where(
                        LessonFeedback.profile_id == profile.id, LessonFeedback.unit_id == unit_id
                    )
                )
            ).scalar_one_or_none()
        )

    async def save(self, unit_id: UUID, request: FeedbackRequest, auth_user_id: UUID) -> FeedbackResponse:
        profile = await self._profile(auth_user_id)
        unit, task_title, career_slug = await self._lesson(unit_id, profile.id)

        # A reason only means something for a "not helpful" vote.
        reason = request.reason if not request.helpful else None
        comment = (request.comment or "").strip() or None

        values = dict(
            profile_id=profile.id,
            unit_id=unit_id,
            helpful=request.helpful,
            reason=reason,
            comment=comment if not request.helpful else None,
            career_slug=career_slug,
            task_title=task_title,
            lesson_title=unit.title,
            lesson_type=getattr(unit.type, "value", unit.type),
        )

        try:
            # One vote per learner per lesson; voting again replaces it.
            statement = insert(LessonFeedback).values(**values)
            statement = statement.on_conflict_do_update(
                constraint="uq_lesson_feedback_once",
                set_={key: statement.excluded[key] for key in ("helpful", "reason", "comment")},
            )
            await self.db.execute(statement)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        return FeedbackResponse(helpful=request.helpful, reason=reason, comment=values["comment"])

    async def clear(self, unit_id: UUID, auth_user_id: UUID) -> None:
        profile = await self._profile(auth_user_id)
        await self._lesson(unit_id, profile.id)

        try:
            row = (
                await self.db.execute(
                    select(LessonFeedback).where(
                        LessonFeedback.profile_id == profile.id, LessonFeedback.unit_id == unit_id
                    )
                )
            ).scalar_one_or_none()

            if row is not None:
                await self.db.delete(row)

            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
