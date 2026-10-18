import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services.interview_generator import InterviewGenerator
from app.models.interview import InterviewSession, InterviewTurn
from app.repositories.interview_repository import InterviewRepository
from app.repositories.profile_repository import ProfileRepository
from app.schemas.interview import (
    AnswerRequest,
    Averages,
    InterviewSummary,
    SessionListItem,
    SessionListResponse,
    SessionResponse,
    StartInterviewRequest,
    TurnResponse,
)
from app.services.gamification_service import (
    GamificationService,
    REASON_INTERVIEW,
    XP_INTERVIEW_COMPLETED,
)

logger = logging.getLogger(__name__)

MAX_SESSIONS = 30
MAX_ACTIVE_SESSIONS = 3
DIFFICULTIES = {"beginner", "intermediate", "advanced"}


def default_difficulty(skill_level) -> str:
    value = getattr(skill_level, "value", skill_level)

    return value if value in DIFFICULTIES else "beginner"


def compute_scores(turns: list) -> tuple[Averages | None, float | None]:
    """Per-dimension averages (0 to 10) and an overall score (0 to 100)
    over the answered turns. None when nothing has been answered."""
    graded = [t for t in turns if t.technical_score is not None]

    if not graded:
        return None, None

    def mean(values):
        return round(sum(values) / len(values), 1)

    averages = Averages(
        technical=mean([t.technical_score for t in graded]),
        communication=mean([t.communication_score for t in graded]),
        confidence=mean([t.confidence_score for t in graded]),
    )

    overall = round(
        (averages.technical + averages.communication + averages.confidence)
        / 3
        * 10,
        1,
    )

    return averages, overall


class InterviewService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repository = ProfileRepository(db)
        self.repository = InterviewRepository(db)
        self.generator = InterviewGenerator()
        self.gamification = GamificationService(db)

    async def _profile(self, auth_user_id: UUID):
        profile = await self.profile_repository.get_by_auth_user_id(
            auth_user_id
        )

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        return profile

    async def _session(self, session_id: UUID, profile_id: UUID):
        session = await self.repository.get_owned(session_id, profile_id)

        if not session:
            raise HTTPException(status_code=404, detail="Interview not found")

        return session

    async def _detail(self, session: InterviewSession) -> SessionResponse:
        turns = await self.repository.turns(session.id)
        averages, _ = compute_scores(turns)

        return SessionResponse(
            id=session.id,
            role=session.role,
            difficulty=session.difficulty,
            status=session.status,
            overall_score=session.overall_score,
            averages=averages,
            summary=(
                InterviewSummary(**session.summary) if session.summary else None
            ),
            answered=sum(1 for t in turns if t.answer is not None),
            total=len(turns),
            created_at=session.created_at,
            turns=[TurnResponse.model_validate(t) for t in turns],
        )

    async def _commit(self):
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    async def start(
        self,
        payload: StartInterviewRequest,
        auth_user_id: UUID,
    ) -> SessionResponse:
        profile = await self._profile(auth_user_id)

        total, active = await self.repository.count_sessions(profile.id)

        if total >= MAX_SESSIONS:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"You can keep up to {MAX_SESSIONS} interviews. "
                    "Delete an old one to start another."
                ),
            )

        if active >= MAX_ACTIVE_SESSIONS:
            raise HTTPException(
                status_code=409,
                detail="Finish or delete an unfinished interview first.",
            )

        difficulty = payload.difficulty or default_difficulty(
            profile.skill_level
        )

        try:
            questions = await self.generator.questions(
                role=payload.role,
                difficulty=difficulty,
                career=profile.career_slug,
            )
        except Exception as exc:
            logger.exception("Interview question generation failed")
            raise HTTPException(
                status_code=502,
                detail="Could not prepare the interview right now. Try again.",
            ) from exc

        session = InterviewSession(
            profile_id=profile.id,
            role=payload.role,
            difficulty=difficulty,
            status="in_progress",
        )

        turns = [
            InterviewTurn(order=index, question=question)
            for index, question in enumerate(questions, start=1)
        ]

        try:
            await self.repository.create(session, turns)
            await self.db.commit()
            await self.db.refresh(session)
        except Exception:
            await self.db.rollback()
            raise

        return await self._detail(session)

    async def list(self, auth_user_id: UUID) -> SessionListResponse:
        profile = await self._profile(auth_user_id)
        rows = await self.repository.list_for_profile(profile.id)

        return SessionListResponse(
            sessions=[
                SessionListItem(
                    id=s.id,
                    role=s.role,
                    difficulty=s.difficulty,
                    status=s.status,
                    overall_score=s.overall_score,
                    answered=int(answered),
                    total=int(total),
                    created_at=s.created_at,
                )
                for s, answered, total in rows
            ]
        )

    async def get(self, session_id: UUID, auth_user_id: UUID):
        profile = await self._profile(auth_user_id)

        return await self._detail(await self._session(session_id, profile.id))

    async def answer(
        self,
        session_id: UUID,
        order: int,
        payload: AnswerRequest,
        auth_user_id: UUID,
    ) -> TurnResponse:
        profile = await self._profile(auth_user_id)
        session = await self._session(session_id, profile.id)

        if session.status != "in_progress":
            raise HTTPException(
                status_code=409, detail="This interview is already finished."
            )

        # Locked so a double submit cannot be graded twice.
        turn = await self.repository.get_turn(
            session.id, order, for_update=True
        )

        if not turn:
            raise HTTPException(status_code=404, detail="Question not found")

        if turn.answer is not None:
            raise HTTPException(
                status_code=409, detail="You already answered this question."
            )

        try:
            graded = await self.generator.grade(
                role=session.role,
                difficulty=session.difficulty,
                question=turn.question,
                answer=payload.answer,
            )
        except Exception as exc:
            await self.db.rollback()
            logger.exception("Interview grading failed")
            raise HTTPException(
                status_code=502,
                detail="Could not review your answer right now. Try again.",
            ) from exc

        turn.answer = payload.answer
        turn.feedback = graded.feedback
        turn.technical_score = graded.technical
        turn.communication_score = graded.communication
        turn.confidence_score = graded.confidence
        turn.answered_at = datetime.now(timezone.utc)

        await self._commit()
        await self.db.refresh(turn)

        return TurnResponse.model_validate(turn)

    async def finish(
        self,
        session_id: UUID,
        auth_user_id: UUID,
    ) -> SessionResponse:
        profile = await self._profile(auth_user_id)
        session = await self._session(session_id, profile.id)

        if session.status == "completed":
            return await self._detail(session)

        turns = await self.repository.turns(session.id)
        answered = [t for t in turns if t.answer is not None]

        if not answered:
            raise HTTPException(
                status_code=422,
                detail="Answer at least one question before finishing.",
            )

        _, overall = compute_scores(answered)

        # The coaching summary is a nice-to-have; scores still count if the
        # AI is unavailable.
        try:
            summary = await self.generator.summarize(
                role=session.role,
                difficulty=session.difficulty,
                answered_turns=answered,
            )
            session.summary = summary.model_dump()
        except Exception:
            logger.exception("Interview summary failed")

        session.overall_score = overall
        session.status = "completed"

        await self.gamification.award(
            profile=profile,
            amount=XP_INTERVIEW_COMPLETED,
            reason=REASON_INTERVIEW,
            ref_id=session.id,
        )

        await self._commit()
        await self.db.refresh(session)

        return await self._detail(session)

    async def delete(self, session_id: UUID, auth_user_id: UUID) -> None:
        profile = await self._profile(auth_user_id)
        session = await self._session(session_id, profile.id)

        await self.repository.delete(session)
        await self._commit()
