from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import InterviewSession, InterviewTurn


class InterviewRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def count_sessions(self, profile_id: UUID) -> tuple[int, int]:
        """(all sessions, sessions still in progress)."""
        result = await self.db.execute(
            select(
                func.count(),
                func.count().filter(InterviewSession.status == "in_progress"),
            ).where(InterviewSession.profile_id == profile_id)
        )

        total, active = result.one()

        return int(total), int(active)

    async def create(
        self,
        session: InterviewSession,
        turns: list[InterviewTurn],
    ) -> InterviewSession:
        self.db.add(session)
        await self.db.flush()

        for turn in turns:
            turn.session_id = session.id

        self.db.add_all(turns)
        await self.db.flush()

        return session

    async def get_owned(
        self,
        session_id: UUID,
        profile_id: UUID,
    ) -> InterviewSession | None:
        result = await self.db.execute(
            select(InterviewSession).where(
                InterviewSession.id == session_id,
                InterviewSession.profile_id == profile_id,
            )
        )

        return result.scalar_one_or_none()

    async def turns(self, session_id: UUID) -> list[InterviewTurn]:
        result = await self.db.execute(
            select(InterviewTurn)
            .where(InterviewTurn.session_id == session_id)
            .order_by(InterviewTurn.order.asc())
        )

        return list(result.scalars().all())

    async def get_turn(
        self,
        session_id: UUID,
        order: int,
        for_update: bool = False,
    ) -> InterviewTurn | None:
        stmt = select(InterviewTurn).where(
            InterviewTurn.session_id == session_id,
            InterviewTurn.order == order,
        )

        if for_update:
            stmt = stmt.with_for_update()

        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def list_for_profile(self, profile_id: UUID):
        """(session, answered, total) per session, newest first."""
        answered = func.count(InterviewTurn.answer)
        total = func.count(InterviewTurn.id)

        result = await self.db.execute(
            select(InterviewSession, answered, total)
            .outerjoin(
                InterviewTurn,
                InterviewTurn.session_id == InterviewSession.id,
            )
            .where(InterviewSession.profile_id == profile_id)
            .group_by(InterviewSession.id)
            .order_by(InterviewSession.created_at.desc())
        )

        return result.all()

    async def delete(self, session: InterviewSession) -> None:
        await self.db.delete(session)
        await self.db.flush()
