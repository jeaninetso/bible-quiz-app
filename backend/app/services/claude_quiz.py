"""Generates quiz questions and fun facts about a passage using Claude,
grounded in the real ESV text fetched by esv_client.py — the LLM is given
the passage and asked to write questions ABOUT it, never asked to recite
Scripture from its own training data.

Defense-in-depth against verbatim recitation (accuracy + copyright): the
system prompt forbids quoting the passage directly, and _verbatim_overlap()
independently checks Claude's output for long word-for-word runs lifted from
the source text. A violation (or malformed output — wrong question/option
count) triggers a bounded retry, never an unbounded loop. Retries tell Claude
exactly what was rejected and why — a blind identical retry tends to just
reproduce the same violation, especially for short famous phrases that are
genuinely the most natural wording.
"""

import re

import anthropic
from pydantic import BaseModel, Field, ValidationError

from app.config import ANTHROPIC_API_KEY, QUIZ_MODEL

QUESTION_COUNT = 5
QUESTION_COUNT_MAX = 6  # broad passages (e.g. multi-psalm Psalms sections) can
# legitimately need one extra question to cover the material — allow it
# rather than retrying against a hard cap Claude keeps overrunning.
OPTIONS_PER_QUESTION = 4
FUN_FACT_COUNT = 2
MAX_RETRIES = 3  # up to 4 total attempts — retries now include corrective
# feedback naming the exact violation, so each one has a real shot at fixing
# it rather than blindly reproducing the same text

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
    questions: list[QuizQuestion] = Field(min_length=QUESTION_COUNT, max_length=QUESTION_COUNT_MAX)
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


# All 66 book names (+ common singular aliases like "Psalm"/"Proverb" for
# "Psalm 2"/"Proverb 3" phrasing) — used only to detect an explicit citation
# like "Psalm 2" or "Job 2:11" in generated text. A verbatim run is fine when
# it's an attributed quote of a specific reference rather than passed off as
# original phrasing; it's not fine when there's no citation to anchor it.
_BOOK_NAMES = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth",
    "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles",
    "Ezra", "Nehemiah", "Esther", "Job", "Psalms", "Psalm", "Proverbs", "Proverb",
    "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations", "Ezekiel",
    "Daniel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk",
    "Zephaniah", "Haggai", "Zechariah", "Malachi", "Matthew", "Mark", "Luke", "John",
    "Acts", "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians", "1 Timothy",
    "2 Timothy", "Titus", "Philemon", "Hebrews", "James", "1 Peter", "2 Peter",
    "1 John", "2 John", "3 John", "Jude", "Revelation",
]
_CITATION_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(name) for name in _BOOK_NAMES) + r")\s+\d+(:\d+(-\d+)?)?\b"
)


def _has_citation(text: str) -> bool:
    return bool(_CITATION_PATTERN.search(text))


def _find_verbatim_violation(passage_text: str, result: QuizGenerationResult) -> str | None:
    for q in result.questions:
        if not _has_citation(q.question) and _verbatim_overlap(passage_text, q.question):
            return f"question copies passage text verbatim: {q.question!r}"
        if not _has_citation(q.explanation) and _verbatim_overlap(passage_text, q.explanation):
            return f"explanation copies passage text verbatim: {q.explanation!r}"
        for option in q.options:
            if not _has_citation(option) and _verbatim_overlap(passage_text, option):
                return f"answer option copies passage text verbatim: {option!r}"
    for fact in result.fun_facts:
        if not _has_citation(fact.fact) and _verbatim_overlap(passage_text, fact.fact):
            return f"fun fact copies passage text verbatim: {fact.fact!r}"
    return None


SYSTEM_PROMPT = f"""You are a Bible quiz writer for a Scripture memory app. You will be given \
the full ESV text of a Bible passage. Write a quiz about its content.

Rules:
- Write {QUESTION_COUNT} multiple-choice questions (up to {QUESTION_COUNT_MAX} if \
the passage is broad enough to need it — never fewer than {QUESTION_COUNT}, never \
more than {QUESTION_COUNT_MAX}), each with exactly {OPTIONS_PER_QUESTION} options \
and one correct answer (correct_index, 0-based).
- Write exactly {FUN_FACT_COUNT} fun facts about the passage (historical context, \
literary details, cross-references elsewhere in Scripture, etc.).
- Every question must test comprehension of the given passage — never ask about \
verses outside it.
- Paraphrase in your own words for questions, options, explanations, and fun \
facts — don't quote the passage verbatim without attribution. Long word-for-word \
copies from the source text will be automatically rejected UNLESS the text \
explicitly cites the specific reference being quoted (e.g. "According to Psalm \
2, ..." or "Job 2:11 says ..."). A cited quote is fine; an uncited one is not. \
If you need to reference specific names or epithets that can't be paraphrased \
(e.g. "Eliphaz the Temanite"), either cite the verse instead of repeating the \
phrase — e.g. "Job's three friends (Job 2:11)" — or quote it with a citation.
- Each explanation should briefly justify why the correct answer is right.
- Vary question difficulty and style (who/what/where/why, sequence of events, \
character motivations, thematic significance)."""


def generate_quiz(passage_text: str, reference: str) -> QuizGenerationResult:
    if not ANTHROPIC_API_KEY:
        raise ClaudeQuizError("ANTHROPIC_API_KEY is not set — copy backend/.env.example to .env and fill it in.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    base_prompt = f"Passage: {reference} (ESV)\n\n{passage_text}"
    last_error = "unknown error"
    for attempt in range(MAX_RETRIES + 1):
        user_content = base_prompt
        if attempt > 0:
            # Blindly resending the same request tends to reproduce the same
            # violation verbatim — a short, famous phrase is often genuinely
            # the most natural wording, so Claude regenerates it unprompted.
            # Naming exactly what was rejected gives it something to fix.
            user_content += (
                f"\n\nYour previous attempt was rejected for this reason: {last_error}\n"
                "Rewrite so this specific violation doesn't recur — reword that "
                "text further, or restructure the question/option so the exact "
                "wording isn't needed. (Note: an answer option can't cite a verse "
                "reference inline without giving away which option is correct — "
                "if the violation was in an option, paraphrase it instead.)"
            )
        try:
            response = client.messages.parse(
                model=QUIZ_MODEL,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
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
