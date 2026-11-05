"""The mock-interview AI: what it is asked, and what it does with unusable answers."""
import asyncio
import json
import selectors
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.ai.services import interview_generator
from app.ai.services.interview_generator import InterviewGenerator, format_results


def run(coro):
    return asyncio.run(coro, loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))


class FakeAI:
    """Stands in for the language model: records what was sent, answers with fixed text."""

    def __init__(self, reply):
        self.reply, self.calls = reply, []

    async def __call__(self, messages, **options):
        self.calls.append({"messages": messages, **options})
        return self.reply if isinstance(self.reply, str) else json.dumps(self.reply)


def use(monkeypatch, reply):
    fake = FakeAI(reply)
    monkeypatch.setattr(interview_generator, "complete_text", fake)
    return fake


QUESTIONS = [f"Question number {i}?" for i in range(5)]


def test_it_asks_for_five_questions_for_the_role_and_level(monkeypatch):
    fake = use(monkeypatch, {"questions": QUESTIONS})
    result = run(InterviewGenerator().questions("Backend Engineer", "beginner", "backend-engineer"))

    assert result == QUESTIONS
    sent = fake.calls[0]
    prompt = sent["messages"][1]["content"]
    assert "Backend Engineer" in prompt and "beginner" in prompt and "backend-engineer" in prompt and "5" in prompt
    assert sent["purpose"] == "interview" and sent["json_mode"] is True


def test_a_missing_career_is_written_as_not_specified(monkeypatch):
    fake = use(monkeypatch, {"questions": QUESTIONS})
    run(InterviewGenerator().questions("Designer", "advanced", None))

    assert "not specified" in fake.calls[0]["messages"][1]["content"]


def test_a_reply_wrapped_in_a_code_fence_is_still_understood(monkeypatch):
    use(monkeypatch, "```json\n" + json.dumps({"questions": QUESTIONS}) + "\n```")

    assert run(InterviewGenerator().questions("QA", "beginner", None)) == QUESTIONS


@pytest.mark.parametrize(
    "bad",
    [
        {"questions": QUESTIONS[:4]},                       # too few
        {"questions": QUESTIONS + ["Another?"]},            # too many
        {"questions": ["Same?"] * 5},                       # repeated
        {"questions": ["Fine?", "", "Fine 2?", "Fine 3?", "Fine 4?"]},  # an empty one
    ],
)
def test_unusable_question_lists_are_rejected_not_passed_on(monkeypatch, bad):
    use(monkeypatch, bad)

    with pytest.raises(ValidationError):
        run(InterviewGenerator().questions("QA", "beginner", None))


def test_a_reply_that_is_not_json_fails_loudly(monkeypatch):
    use(monkeypatch, "Sure! Here are some questions...")

    with pytest.raises(json.JSONDecodeError):
        run(InterviewGenerator().questions("QA", "beginner", None))


def test_an_answer_is_graded_on_three_scores(monkeypatch):
    fake = use(monkeypatch, {"technical": 7, "communication": 8, "confidence": 6, "feedback": "Clear, add an example."})
    result = run(InterviewGenerator().grade("Backend Engineer", "beginner", "What is HTTP?", "A protocol."))

    assert (result.technical, result.communication, result.confidence) == (7, 8, 6)
    prompt = fake.calls[0]["messages"][1]["content"]
    assert "What is HTTP?" in prompt and "A protocol." in prompt


@pytest.mark.parametrize("scores", [{"technical": 11}, {"communication": -1}, {"confidence": 100}])
def test_scores_outside_zero_to_ten_are_rejected(monkeypatch, scores):
    reply = {"technical": 5, "communication": 5, "confidence": 5, "feedback": "ok", **scores}
    use(monkeypatch, reply)

    with pytest.raises(ValidationError):
        run(InterviewGenerator().grade("QA", "beginner", "Q?", "A"))


def test_feedback_cannot_be_empty(monkeypatch):
    use(monkeypatch, {"technical": 5, "communication": 5, "confidence": 5, "feedback": ""})

    with pytest.raises(ValidationError):
        run(InterviewGenerator().grade("QA", "beginner", "Q?", "A"))


def turn(order, t, c, f, question="Why?"):
    return SimpleNamespace(order=order, technical_score=t, communication_score=c, confidence_score=f, question=question)


def test_the_results_are_listed_one_line_per_question():
    text = format_results([turn(1, 7, 8, 6, "What is HTTP?"), turn(2, 5, 5, 4, "What is REST?")])

    assert text.splitlines()[0] == "Q1: technical 7, communication 8, confidence 6. Question: What is HTTP?"
    assert len(text.splitlines()) == 2


def test_the_summary_sends_the_results_and_returns_strengths_and_next_steps(monkeypatch):
    fake = use(monkeypatch, {"strengths": ["Clear"], "improvements": ["Examples"], "next_steps": ["Practise REST"]})
    result = run(InterviewGenerator().summarize("QA", "beginner", [turn(1, 7, 8, 6, "What is HTTP?")]))

    assert result.strengths == ["Clear"] and result.next_steps == ["Practise REST"]
    assert "technical 7" in fake.calls[0]["messages"][1]["content"]


def test_a_summary_may_leave_lists_out_but_not_overflow_them(monkeypatch):
    use(monkeypatch, {})

    assert run(InterviewGenerator().summarize("QA", "beginner", [])).strengths == []

    use(monkeypatch, {"strengths": ["a"] * 6})

    with pytest.raises(ValidationError):
        run(InterviewGenerator().summarize("QA", "beginner", []))
