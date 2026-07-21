import anthropic
import httpx
import pytest
from pydantic import ValidationError

from app.services import claude_quiz
from app.services.claude_quiz import ClaudeQuizError, FunFact, QuizGenerationResult, QuizQuestion, generate_quiz


def _valid_result():
    questions = [
        QuizQuestion(
            question=f"Sample question {i}?",
            options=["A", "B", "C", "D"],
            correct_index=0,
            explanation="Because the passage describes it that way.",
        )
        for i in range(claude_quiz.QUESTION_COUNT)
    ]
    fun_facts = [FunFact(fact=f"Fun fact number {i}.") for i in range(claude_quiz.FUN_FACT_COUNT)]
    return QuizGenerationResult(questions=questions, fun_facts=fun_facts)


class FakeResponse:
    def __init__(self, parsed_output):
        self.parsed_output = parsed_output


class FakeMessages:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def parse(self, **kwargs):
        self.calls += 1
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return FakeResponse(response)


class FakeClient:
    def __init__(self, responses):
        self.messages = FakeMessages(responses)


def _patch_client(monkeypatch, responses):
    fake_client = FakeClient(responses)
    monkeypatch.setattr(claude_quiz.anthropic, "Anthropic", lambda api_key: fake_client)
    monkeypatch.setattr(claude_quiz, "ANTHROPIC_API_KEY", "fake-key")
    return fake_client


def test_generate_quiz_returns_result_on_first_success(monkeypatch):
    result = _valid_result()
    fake_client = _patch_client(monkeypatch, [result])

    output = generate_quiz("In the days when the judges ruled...", "Ruth")
    assert output is result
    assert fake_client.messages.calls == 1


def test_generate_quiz_raises_without_api_key(monkeypatch):
    monkeypatch.setattr(claude_quiz, "ANTHROPIC_API_KEY", "")
    with pytest.raises(ClaudeQuizError, match="ANTHROPIC_API_KEY is not set"):
        generate_quiz("passage text", "Ruth")


def test_generate_quiz_raises_immediately_on_api_error(monkeypatch):
    error = anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))
    fake_client = _patch_client(monkeypatch, [error])

    with pytest.raises(ClaudeQuizError, match="Claude API request failed"):
        generate_quiz("passage text", "Ruth")
    assert fake_client.messages.calls == 1  # not retried — a network/API failure won't fix itself


def test_generate_quiz_retries_on_verbatim_overlap_then_succeeds(monkeypatch):
    passage = "In the days when the judges ruled there was a famine in the land of Judah"
    verbatim_result = QuizGenerationResult(
        questions=[
            QuizQuestion(
                question="What happened in the days when the judges ruled there was a famine in the land?",
                options=["A", "B", "C", "D"],
                correct_index=0,
                explanation="See above.",
            )
        ]
        + [
            QuizQuestion(
                question=f"Filler question {i}?",
                options=["A", "B", "C", "D"],
                correct_index=0,
                explanation="Filler.",
            )
            for i in range(claude_quiz.QUESTION_COUNT - 1)
        ],
        fun_facts=[FunFact(fact=f"Fun fact {i}.") for i in range(claude_quiz.FUN_FACT_COUNT)],
    )
    clean_result = _valid_result()
    fake_client = _patch_client(monkeypatch, [verbatim_result, clean_result])

    output = generate_quiz(passage, "Ruth")
    assert output is clean_result
    assert fake_client.messages.calls == 2


def test_generate_quiz_gives_up_after_max_retries(monkeypatch):
    passage = "In the days when the judges ruled there was a famine in the land of Judah"
    verbatim_result = QuizGenerationResult(
        questions=[
            QuizQuestion(
                question="What happened in the days when the judges ruled there was a famine in the land?",
                options=["A", "B", "C", "D"],
                correct_index=0,
                explanation="See above.",
            )
        ]
        + [
            QuizQuestion(
                question=f"Filler question {i}?",
                options=["A", "B", "C", "D"],
                correct_index=0,
                explanation="Filler.",
            )
            for i in range(claude_quiz.QUESTION_COUNT - 1)
        ],
        fun_facts=[FunFact(fact=f"Fun fact {i}.") for i in range(claude_quiz.FUN_FACT_COUNT)],
    )
    fake_client = _patch_client(monkeypatch, [verbatim_result, verbatim_result, verbatim_result])

    with pytest.raises(ClaudeQuizError, match="repeatedly produced invalid"):
        generate_quiz(passage, "Ruth")
    assert fake_client.messages.calls == claude_quiz.MAX_RETRIES + 1


def test_generate_quiz_retries_on_malformed_output(monkeypatch):
    try:
        QuizQuestion.model_validate({})
        raise AssertionError("expected QuizQuestion.model_validate({}) to raise ValidationError")
    except ValidationError as exc:
        bad_output = exc
    fake_client = _patch_client(monkeypatch, [bad_output, _valid_result()])

    output = generate_quiz("passage text", "Ruth")
    assert output is not None
    assert fake_client.messages.calls == 2
