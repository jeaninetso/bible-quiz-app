"""Generates quiz questions and fun facts about a passage using Claude,
grounded in the real ESV text fetched by esv_client.py — the LLM is given
the passage and asked to write questions ABOUT it, never asked to recite
Scripture from its own training data.

Defense-in-depth against verbatim recitation (accuracy + copyright): the
system prompt forbids quoting the passage directly, and _verbatim_overlap()
independently checks Claude's output for long word-for-word runs lifted from
the source text. A violation (or malformed output — wrong question/option
count) triggers a bounded retry, never an unbounded loop.
"""

import re

import anthropic
from pydantic import BaseModel, Field, ValidationError

from app.config import ANTHROPIC_API_KEY, QUIZ_MODEL

QUESTION_COUNT = 5
OPTIONS_PER_QUESTION = 4
FUN_FACT_COUNT = 2
MAX_RETRIES = 2  # up to 3 total attempts

# 8+ consecutive shared words is long enough that it can't be coincidental
# phrasing — it means Claude copied straight from the source passage.
VERBATIM_NGRAM_SIZE = 8


class ClaudeQuizError(Exception):
    pass


class QuizQuestion(BaseModel):
    question: str
    options: list[str] = Field(min_length=OPTIONS_PER_QUESTION, max_length=OPTIONS_PER_QUESTION)
    correct_index: int = Field(ge=0, lt=OPTIONS_PER_QUESTION)
    explanation: str


class FunFact(BaseModel):
    fact: str


class QuizGenerationResult(BaseModel):
    questions: list[QuizQuestion] = Field(min_length=QUESTION_COUNT, max_length=QUESTION_COUNT)
    fun_facts: list[FunFact] = Field(min_length=FUN_FACT_COUNT, max_length=FUN_FACT_COUNT)


def _normalize_words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def _verbatim_overlap(passage_text: str, candidate_text: str) -> bool:
    """True if candidate_text contains a run of VERBATIM_NGRAM_SIZE+
    consecutive words also found (in the same order) in passage_text."""
    source_words = _normalize_words(passage_text)
    candidate_words = _normalize_words(candidate_text)
    if len(candidate_words) < VERBATIM_NGRAM_SIZE:
        return False

    source_ngrams = {
        tuple(source_words[i : i + VERBATIM_NGRAM_SIZE]) for i in range(len(source_words) - VERBATIM_NGRAM_SIZE + 1)
    }
    return any(
        tuple(candidate_words[i : i + VERBATIM_NGRAM_SIZE]) in source_ngrams
        for i in range(len(candidate_words) - VERBATIM_NGRAM_SIZE + 1)
    )


def _find_verbatim_violation(passage_text: str, result: QuizGenerationResult) -> str | None:
    for q in result.questions:
        if _verbatim_overlap(passage_text, q.question) or _verbatim_overlap(passage_text, q.explanation):
            return f"question copies passage text verbatim: {q.question!r}"
        for option in q.options:
            if _verbatim_overlap(passage_text, option):
                return f"answer option copies passage text verbatim: {option!r}"
    for fact in result.fun_facts:
        if _verbatim_overlap(passage_text, fact.fact):
            return f"fun fact copies passage text verbatim: {fact.fact!r}"
    return None


SYSTEM_PROMPT = f"""You are a Bible quiz writer for a Scripture memory app. You will be given \
the full ESV text of a Bible passage. Write a quiz about its content.

Rules:
- Write exactly {QUESTION_COUNT} multiple-choice questions, each with exactly \
{OPTIONS_PER_QUESTION} options and one correct answer (correct_index, 0-based).
- Write exactly {FUN_FACT_COUNT} fun facts about the passage (historical context, \
literary details, cross-references elsewhere in Scripture, etc.).
- Every question must test comprehension of the given passage — never ask about \
verses outside it.
- NEVER quote the passage verbatim. Paraphrase in your own words for questions, \
options, explanations, and fun facts. Long word-for-word copies from the source \
text will be automatically rejected.
- Each explanation should briefly justify why the correct answer is right.
- Vary question difficulty and style (who/what/where/why, sequence of events, \
character motivations, thematic significance)."""


def generate_quiz(passage_text: str, reference: str) -> QuizGenerationResult:
    if not ANTHROPIC_API_KEY:
        raise ClaudeQuizError("ANTHROPIC_API_KEY is not set — copy backend/.env.example to .env and fill it in.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    last_error = "unknown error"
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.messages.parse(
                model=QUIZ_MODEL,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": f"Passage: {reference} (ESV)\n\n{passage_text}",
                    }
                ],
                output_format=QuizGenerationResult,
            )
        except anthropic.APIError as exc:
            # Network/auth/rate-limit/server errors are fatal — retrying a
            # bad request or an outage wastes calls without changing anything.
            raise ClaudeQuizError(f"Claude API request failed: {exc}") from exc
        except ValidationError as exc:
            last_error = f"malformed output: {exc}"
            continue

        result = response.parsed_output
        violation = _find_verbatim_violation(passage_text, result)
        if violation is None:
            return result

        last_error = violation

    raise ClaudeQuizError(f"Claude repeatedly produced invalid quiz output: {last_error}")
