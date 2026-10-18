import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.ai.schemas.interview_schema import (
    AnswerFeedbackOutput,
    QuestionsOutput,
)
from app.schemas.interview import AnswerRequest, StartInterviewRequest
from app.services.interview_service import (
    InterviewService,
    MAX_ACTIVE_SESSIONS,
    compute_scores,
    default_difficulty,
)


def qs(n=5):
    return [f"Question {i}?" for i in range(n)]


def test_questions_need_exactly_five_distinct():
    assert len(QuestionsOutput(questions=qs()).questions) == 5

    with pytest.raises(ValidationError):
        QuestionsOutput(questions=qs(4))

    with pytest.raises(ValidationError):
        QuestionsOutput(questions=["Same?"] * 5)

    with pytest.raises(ValidationError):
        QuestionsOutput(questions=["", "a", "b", "c", "d"])


def test_feedback_scores_are_bounded():
    AnswerFeedbackOutput(technical=0, communication=10, confidence=5, feedback="ok")

    with pytest.raises(ValidationError):
        AnswerFeedbackOutput(technical=11, communication=5, confidence=5, feedback="x")

    with pytest.raises(ValidationError):
        AnswerFeedbackOutput(technical=5, communication=5, confidence=-1, feedback="x")


def test_request_validation():
    assert StartInterviewRequest(role="  QA Engineer ").role == "QA Engineer"

    with pytest.raises(ValidationError):
        StartInterviewRequest(role="x")

    with pytest.raises(ValidationError):
        StartInterviewRequest(role="QA", difficulty="impossible")

    with pytest.raises(ValidationError):
        AnswerRequest(answer="   ")


def test_default_difficulty():
    assert default_difficulty(SimpleNamespace(value="advanced")) == "advanced"
    assert default_difficulty("intermediate") == "intermediate"
    assert default_difficulty(None) == "beginner"
    assert default_difficulty("expert") == "beginner"


def graded(t, c, f, answer="a"):
    return SimpleNamespace(
        technical_score=t, communication_score=c, confidence_score=f, answer=answer
    )


def test_compute_scores():
    averages, overall = compute_scores([graded(8, 6, 7), graded(6, 8, 5)])

    assert averages.technical == 7.0
    assert averages.communication == 7.0
    assert averages.confidence == 6.0
    assert overall == 66.7


def test_compute_scores_ignores_unanswered_and_handles_none():
    unanswered = SimpleNamespace(
        technical_score=None, communication_score=None, confidence_score=None, answer=None
    )

    assert compute_scores([]) == (None, None)
    assert compute_scores([unanswered]) == (None, None)
    assert compute_scores([unanswered, graded(10, 10, 10)])[1] == 100.0


class _Db:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1

    async def refresh(self, obj):
        obj.id = getattr(obj, "id", None) or uuid4()
        if hasattr(obj, "created_at") and obj.created_at is None:
            obj.created_at = datetime.now(timezone.utc)


class _Repo:
    def __init__(self, session=None, total=0, active=0):
        self.session = session
        self.counts = (total, active)
        self.turn_rows = []
        self.created = None

    async def count_sessions(self, profile_id):
        return self.counts

    async def create(self, session, turns):
        session.id = uuid4()
        session.created_at = datetime.now(timezone.utc)
        for t in turns:
            t.session_id = session.id
            t.answer = t.feedback = None
            t.technical_score = t.communication_score = t.confidence_score = None
        self.session = session
        self.turn_rows = turns
        self.created = session
        return session

    async def get_owned(self, session_id, profile_id):
        return self.session

    async def turns(self, session_id):
        return self.turn_rows

    async def get_turn(self, session_id, order, for_update=False):
        return next((t for t in self.turn_rows if t.order == order), None)


class _Profiles:
    async def get_by_auth_user_id(self, auth_user_id):
        return SimpleNamespace(
            id=uuid4(), skill_level=SimpleNamespace(value="beginner"), career_slug="backend"
        )


class _Gen:
    def __init__(self, fail=None, summary_fails=False):
        self.fail = fail
        self.summary_fails = summary_fails

    async def questions(self, role, difficulty, career):
        if self.fail == "questions":
            raise RuntimeError("boom")
        return qs()

    async def grade(self, role, difficulty, question, answer):
        if self.fail == "grade":
            raise RuntimeError("boom")
        return AnswerFeedbackOutput(
            technical=8, communication=6, confidence=7, feedback="Good."
        )

    async def summarize(self, role, difficulty, answered_turns):
        if self.summary_fails:
            raise RuntimeError("boom")
        from app.ai.schemas.interview_schema import SummaryOutput

        return SummaryOutput(strengths=["Clear"], improvements=["Depth"], next_steps=["Practice"])


def _service(repo, gen=None):
    service = InterviewService.__new__(InterviewService)
    service.db = _Db()
    service.profile_repository = _Profiles()
    service.repository = repo
    service.generator = gen or _Gen()
    service.gamification = SimpleNamespace(award=None)
    return service


def _started(service):
    return asyncio.run(
        service.start(StartInterviewRequest(role="Backend Developer"), uuid4())
    )


def test_start_creates_five_unanswered_questions():
    repo = _Repo()
    result = _started(_service(repo))

    assert result.total == 5
    assert result.answered == 0
    assert result.difficulty == "beginner"
    assert [t.order for t in result.turns] == [1, 2, 3, 4, 5]
    assert result.status == "in_progress"


def test_start_refuses_too_many_unfinished():
    service = _service(_Repo(active=MAX_ACTIVE_SESSIONS))

    with pytest.raises(HTTPException) as exc:
        _started(service)

    assert exc.value.status_code == 409


def test_start_ai_failure_is_502_and_saves_nothing():
    repo = _Repo()
    service = _service(repo, _Gen(fail="questions"))

    with pytest.raises(HTTPException) as exc:
        _started(service)

    assert exc.value.status_code == 502
    assert repo.created is None
    assert service.db.commits == 0


def _answer(service, session_id, order=1, text="My answer"):
    return asyncio.run(
        service.answer(session_id, order, AnswerRequest(answer=text), uuid4())
    )


def test_answer_is_graded_and_stored():
    repo = _Repo()
    service = _service(repo)
    started = _started(service)

    turn = _answer(service, started.id)

    assert turn.technical_score == 8
    assert turn.feedback == "Good."
    assert repo.turn_rows[0].answer == "My answer"


def test_answering_twice_is_a_conflict():
    service = _service(_Repo())
    started = _started(service)
    _answer(service, started.id)

    with pytest.raises(HTTPException) as exc:
        _answer(service, started.id)

    assert exc.value.status_code == 409


def test_unknown_question_is_404():
    service = _service(_Repo())
    started = _started(service)

    with pytest.raises(HTTPException) as exc:
        _answer(service, started.id, order=9)

    assert exc.value.status_code == 404


def test_grading_failure_is_502_and_answer_not_saved():
    repo = _Repo()
    service = _service(repo)
    started = _started(service)
    service.generator = _Gen(fail="grade")

    with pytest.raises(HTTPException) as exc:
        _answer(service, started.id)

    assert exc.value.status_code == 502
    assert repo.turn_rows[0].answer is None


def test_finish_needs_at_least_one_answer():
    service = _service(_Repo())
    started = _started(service)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.finish(started.id, uuid4()))

    assert exc.value.status_code == 422


def _finish(service, session_id, awards):
    async def award(**kwargs):
        awards.append(kwargs["reason"])
        return True

    service.gamification = SimpleNamespace(award=award)
    return asyncio.run(service.finish(session_id, uuid4()))


def test_finish_scores_summarizes_and_awards_xp():
    service = _service(_Repo())
    started = _started(service)
    _answer(service, started.id, order=1)
    _answer(service, started.id, order=2)
    awards = []

    result = _finish(service, started.id, awards)

    assert result.status == "completed"
    assert result.overall_score == 70.0  # (8 + 6 + 7) / 3 * 10
    assert result.summary.strengths == ["Clear"]
    assert result.answered == 2
    assert awards == ["interview_completed"]


def test_finish_still_works_when_summary_fails():
    service = _service(_Repo())
    started = _started(service)
    _answer(service, started.id)
    service.generator = _Gen(summary_fails=True)

    result = _finish(service, started.id, [])

    assert result.status == "completed"
    assert result.summary is None
    assert result.overall_score == 70.0


def test_finish_is_idempotent_and_does_not_award_twice():
    service = _service(_Repo())
    started = _started(service)
    _answer(service, started.id)
    awards = []

    _finish(service, started.id, awards)
    again = _finish(service, started.id, awards)

    assert again.status == "completed"
    assert awards == ["interview_completed"]


def test_cannot_answer_after_finishing():
    service = _service(_Repo())
    started = _started(service)
    _answer(service, started.id)
    _finish(service, started.id, [])

    with pytest.raises(HTTPException) as exc:
        _answer(service, started.id, order=2)

    assert exc.value.status_code == 409
