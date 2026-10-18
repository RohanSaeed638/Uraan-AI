import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.ai.schemas.quiz_schema import QuizOutput
from app.schemas.quiz import QuizAnswerRequest, QuizSubmitRequest
from app.services.quiz_service import QuizService


def _question(correct_option=1, options=None):
    return {
        "question": "What does HTTP stand for?",
        "options": options or ["a", "b", "c", "d"],
        "correct_option": correct_option,
        "explanation": "Because.",
    }


def test_quiz_output_accepts_valid_payload():
    assert len(QuizOutput(questions=[_question()]).questions) == 1


@pytest.mark.parametrize(
    "bad",
    [
        _question(options=["a", "b", "c"]),
        _question(options=["a", "a", "c", "d"]),
        _question(correct_option=4),
    ],
)
def test_quiz_output_rejects_invalid_questions(bad):
    with pytest.raises(ValidationError):
        QuizOutput(questions=[bad])


class _FakeDb:
    def __init__(self):
        self.committed = False

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass


class _FakeQuizRepository:
    def __init__(self, questions):
        self.questions = questions
        self.attempts = []

    async def get_questions(self, task_id):
        return self.questions

    async def create_attempt(self, attempt):
        attempt.id = uuid4()
        self.attempts.append(attempt)
        return attempt


def _service(questions):
    service = QuizService.__new__(QuizService)
    service.db = _FakeDb()
    service.quiz_repository = _FakeQuizRepository(questions)

    async def fake_validate(task_id, auth_user_id):
        return SimpleNamespace(id=uuid4())

    service._get_profile_and_validate_task = fake_validate
    return service


def _questions(count=5):
    return [
        SimpleNamespace(
            id=uuid4(),
            question=f"Q{i}",
            options=["a", "b", "c", "d"],
            correct_option=0,
            explanation=None,
            order=i,
        )
        for i in range(count)
    ]


def _submit(service, questions, picks):
    payload = QuizSubmitRequest(
        answers=[
            QuizAnswerRequest(question_id=q.id, selected_option=pick)
            for q, pick in zip(questions, picks)
        ]
    )
    return asyncio.run(service.submit(uuid4(), payload, uuid4()))


def test_submit_passes_at_seventy_percent():
    questions = _questions(10)
    service = _service(questions)

    result = _submit(service, questions, [0] * 7 + [1] * 3)

    assert result.correct_answers == 7
    assert result.score_percentage == 70.0
    assert result.passed
    assert service.db.committed
    assert len(service.quiz_repository.attempts) == 1


def test_submit_fails_below_threshold():
    questions = _questions(5)
    service = _service(questions)

    result = _submit(service, questions, [0, 0, 0, 1, 1])

    assert result.score_percentage == 60.0
    assert not result.passed


def test_submit_requires_an_answer_for_every_question():
    questions = _questions(3)
    service = _service(questions)
    payload = QuizSubmitRequest(
        answers=[
            QuizAnswerRequest(question_id=questions[0].id, selected_option=0)
        ]
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.submit(uuid4(), payload, uuid4()))

    assert exc.value.status_code == 422


def test_submit_rejects_out_of_range_option():
    questions = _questions(2)
    service = _service(questions)

    with pytest.raises(HTTPException) as exc:
        _submit(service, questions, [0, 9])

    assert exc.value.status_code == 422
