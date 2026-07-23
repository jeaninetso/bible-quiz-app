from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

# Every response model mirrors the frontend's TS types field-for-field
# (including key casing) so the frontend's Zod schemas can validate this
# API's JSON with zero changes.


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class LoginRequest(BaseModel):
    username: str
    password: str = Field(repr=False)  # never echoed back in logs/errors


class UserOut(CamelModel):
    username: str


class SectionOut(CamelModel):
    id: int
    book_id: int
    name: str
    is_available: bool


class BookOut(CamelModel):
    id: int
    code: str
    name: str
    testament: str
    chapter_count: int
    is_available: bool
    sections: list[SectionOut] = []


class QuestionOut(CamelModel):
    """Client-safe view of a quiz question — correct_index/explanation are
    deliberately omitted so the answer key never reaches the browser until
    after submission (see QuizAttempt.questions_json)."""

    question: str
    options: list[str]


class FunFactOut(CamelModel):
    fact: str


class QuizAttemptOut(CamelModel):
    id: int
    book_id: int
    book_name: str
    section_id: int | None = None
    section_name: str | None = None
    chapter_reference: str
    questions: list[QuestionOut]
    fun_facts: list[FunFactOut]


class SubmitQuizRequest(BaseModel):
    # One entry per question, in order; None for a question left unanswered.
    answers: list[int | None]


class QuestionResultOut(CamelModel):
    """Post-submission view of a question — now safe to include the answer
    key, since scoring has already happened server-side."""

    question: str
    options: list[str]
    correct_index: int
    explanation: str
    selected_index: int | None
    is_correct: bool


class BadgeOut(CamelModel):
    code: str
    name: str
    description: str


class UserBookProgressOut(CamelModel):
    xp: int
    level: int
    current_streak: int
    longest_streak: int
    best_score: int
    quizzes_completed: int


class QuizResultOut(CamelModel):
    id: int
    score: int
    total_questions: int
    questions: list[QuestionResultOut]
    xp_earned: int
    progress: UserBookProgressOut
    new_badges: list[BadgeOut]


class EarnedBadgeOut(CamelModel):
    code: str
    name: str
    description: str
    earned_at: datetime


class MeStatsOut(CamelModel):
    total_xp: int
    level: int
    current_streak: int
    longest_streak: int
    quizzes_completed: int
    badges: list[EarnedBadgeOut]


class QuizHistoryItemOut(CamelModel):
    id: int
    book_id: int
    book_name: str
    section_id: int | None = None
    section_name: str | None = None
    chapter_reference: str
    score: int
    total_questions: int
    submitted_at: datetime


class QuizReviewOut(CamelModel):
    """Read-only replay of a completed attempt — same per-question shape as
    QuizResultOut, but without xp_earned/progress/new_badges, which describe
    a one-time submission event rather than durable history."""

    id: int
    book_name: str
    section_id: int | None = None
    section_name: str | None = None
    chapter_reference: str
    score: int
    total_questions: int
    submitted_at: datetime
    questions: list[QuestionResultOut]
