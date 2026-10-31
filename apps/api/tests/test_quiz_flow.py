"""Quiz access, first-time generation and the submit rules not covered in test_quiz.py."""
import asyncio
import selectors
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.ai.schemas.quiz_schema import QuizOutput
from app.schemas.quiz import QuizAnswerRequest, QuizSubmitRequest
from app.services import quiz_service
from app.services.quiz_service import QuizService


def run(coro):
    return asyncio.run(coro, loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


class Db:
    def __init__(self):
        self.commits = self.rollbacks = 0

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1


class Profiles:
    def __init__(self, profile):
        self.profile = profile

    async def get_by_auth_user_id(self, _):
        return self.profile


class Quizzes:
    def __init__(self, questions=(), owned=True, fail_create=False, fail_attempt=False):
        self.questions = list(questions)
        self.owned, self.fail_create, self.fail_attempt = owned, fail_create, fail_attempt
        self.created = None
        self.attempts = []

    async def get_owned_task(self, task_id, profile_id):
        return SimpleNamespace(id=task_id) if self.owned else None

    async def get_questions(self, task_id):
        return self.questions

    async def create_quiz_with_questions(self, quiz, questions):
        if self.fail_create:
            raise RuntimeError("write failed")

        self.created = (quiz, questions)
        # What the database would return after saving.
        self.questions = [
            SimpleNamespace(id=uuid4(), question=q.question, options=q.options, order=q.order,
                            correct_option=q.correct_option, explanation=q.explanation)
            for q in questions
        ]

    async def create_attempt(self, attempt):
        if self.fail_attempt:
            raise RuntimeError("write failed")

        attempt.id = uuid4()
        self.attempts.append(attempt)


class Tasks:
    async def get_task_for_user(self, task_id, profile_id):
        return SimpleNamespace(id=task_id, title="Learn HTTP")


class Generator:
    def __init__(self, output=None, error=None):
        self.output, self.error = output, error

    async def generate(self, profile, task):
        if self.error:
            raise self.error

        return self.output


OUTPUT = QuizOutput(
    questions=[
        {"question": f"Question {i}?", "options": ["a", "b", "c", "d"], "correct_option": i % 4, "explanation": "because"}
        for i in range(5)
    ]
)


def make(quizzes=None, profile=True, generator=None):
    service = QuizService.__new__(QuizService)
    service.db = Db()
    service.profile_repository = Profiles(SimpleNamespace(id=uuid4(), language="en") if profile else None)
    service.quiz_repository = quizzes or Quizzes()
    service.task_repository = Tasks()
    service.generator = generator or Generator(OUTPUT)
    return service


@pytest.fixture(autouse=True)
def no_ai_context(monkeypatch):
    monkeypatch.setattr(quiz_service, "use_profile", lambda *a, **k: None)


def one_answer():
    return QuizSubmitRequest(answers=[QuizAnswerRequest(question_id=uuid4(), selected_option=0)])


def refused(call, status):
    with pytest.raises(HTTPException) as caught:
        run(call)

    assert caught.value.status_code == status


# ---- access ----------------------------------------------------------------------------------------------------------------


def test_a_quiz_needs_a_profile_and_a_task_the_learner_owns():
    refused(make(profile=False).get_questions(uuid4(), uuid4()), 404)
    refused(make(Quizzes(owned=False)).get_questions(uuid4(), uuid4()), 404)
    refused(make(Quizzes(owned=False)).submit(uuid4(), one_answer(), uuid4()), 404)


# ---- reading and generating -----------------------------------------------------------------------------------------------------


def test_existing_questions_are_shown_without_the_answers():
    questions = [SimpleNamespace(id=uuid4(), question="Q", options=["a", "b", "c", "d"], order=0, correct_option=2)]
    shown = run(make(Quizzes(questions)).get_questions(uuid4(), uuid4()))

    assert len(shown) == 1 and not hasattr(shown[0], "correct_option")


def test_the_first_visit_generates_and_saves_the_quiz_then_shows_it():
    quizzes = Quizzes()
    service = make(quizzes)
    shown = run(service.get_questions(uuid4(), uuid4()))

    quiz, saved = quizzes.created
    assert quiz.title == "Learn HTTP quiz" and quiz.passing_score == 70
    assert [q.order for q in saved] == [0, 1, 2, 3, 4]
    assert len(shown) == 5 and service.db.commits == 1


def test_an_ai_failure_is_a_502_and_saves_nothing():
    quizzes = Quizzes()
    service = make(quizzes, generator=Generator(error=RuntimeError("model down")))
    refused(service.get_questions(uuid4(), uuid4()), 502)

    assert quizzes.created is None and service.db.commits == 0


def test_a_failed_save_of_a_new_quiz_is_rolled_back():
    service = make(Quizzes(fail_create=True))

    with pytest.raises(RuntimeError):
        run(service.get_questions(uuid4(), uuid4()))

    assert service.db.rollbacks == 1 and service.db.commits == 0


# ---- submitting -----------------------------------------------------------------------------------------------------------------


def questions(count=4):
    return [
        SimpleNamespace(id=uuid4(), question=f"Q{i}", options=["a", "b", "c", "d"], correct_option=0,
                        explanation=None, order=i)
        for i in range(count)
    ]


def answer_all(qs, picks):
    return QuizSubmitRequest(answers=[QuizAnswerRequest(question_id=q.id, selected_option=p) for q, p in zip(qs, picks)])


def test_submitting_before_a_quiz_exists_is_a_404():
    refused(make(Quizzes([])).submit(uuid4(), one_answer(), uuid4()), 404)


def test_answering_the_same_question_twice_is_refused():
    qs = questions(2)
    payload = QuizSubmitRequest(
        answers=[QuizAnswerRequest(question_id=qs[0].id, selected_option=0)] * 2
    )
    refused(make(Quizzes(qs)).submit(uuid4(), payload, uuid4()), 422)


def test_answers_for_questions_that_are_not_in_the_quiz_are_refused():
    qs = questions(2)
    payload = answer_all(qs, [0, 0])
    payload.answers[1] = QuizAnswerRequest(question_id=uuid4(), selected_option=0)

    refused(make(Quizzes(qs)).submit(uuid4(), payload, uuid4()), 422)


def test_the_result_says_which_answers_were_right_and_the_attempt_is_saved(awards):
    qs = questions(4)
    quizzes = Quizzes(qs)
    service = make(quizzes)
    result = run(service.submit(uuid4(), answer_all(qs, [0, 0, 0, 1]), uuid4()))

    assert (result.correct_answers, result.total_questions) == (3, 4)
    assert [a.is_correct for a in result.results] == [True, True, True, False]
    assert quizzes.attempts[0].score_percentage == 75.0 and quizzes.attempts[0].passed is True
    assert len(awards) == 1 and service.db.commits == 1


def test_a_failed_attempt_gives_no_xp(awards):
    qs = questions(4)
    result = run(make(Quizzes(qs)).submit(uuid4(), answer_all(qs, [1, 1, 1, 1]), uuid4()))

    assert result.correct_answers == 0 and awards == []


def test_a_failure_while_saving_the_attempt_is_rolled_back(awards):
    qs = questions(2)
    service = make(Quizzes(qs, fail_attempt=True))

    with pytest.raises(RuntimeError):
        run(service.submit(uuid4(), answer_all(qs, [0, 0]), uuid4()))

    assert service.db.rollbacks == 1 and service.db.commits == 0 and awards == []


def test_an_empty_submission_is_refused_by_the_form_itself():
    with pytest.raises(ValueError):
        QuizSubmitRequest(answers=[])
