"""SQLAlchemy models."""

from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Book(Base):
    """Metadata for all 66 books, seeded once by scripts/seed_books.py.
    `is_available` gates which ones the quiz-generation pipeline actually
    serves — only Ruth for the MVP. Seeding all 66 now is cheap (static,
    well-known data) and lets the hub show the full library with
    "coming soon" books rather than just one lonely entry."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Short internal abbreviation (e.g. "Ruth", "1Sam") — not a claim of
    # strict OSIS-standard compliance, just a stable machine key per book.
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    testament: Mapped[str] = mapped_column(String, nullable=False)  # "old" | "new"
    chapter_count: Mapped[int] = mapped_column(Integer, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Section(Base):
    """A quizzable chapter range within a Book. Exists because the ESV API
    hard-caps any single contiguous range request at half a book's verses
    (or 500, whichever is less) — no book can ever be fetched or quizzed on
    whole, so every quiz target is a Section, never a Book directly.

    Section-level progress/mastery badges were considered and deliberately
    deferred — UserBookProgress stays book-scoped (see its docstring); add a
    separate SectionProgress table later if per-section mastery is wanted."""

    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    # ESV API query string for this range, e.g. "Ruth 1-2" — kept separate
    # from `name` even though they're identical today, in case a section is
    # ever given a purely thematic display name distinct from its reference.
    reference: Mapped[str] = mapped_column(String, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class PassageCache(Base):
    """Short-TTL cache of fetched ESV text only — never the Claude-generated
    quiz output, or retakes would stop being fresh. Kept short-lived (not a
    permanent archive) per the ESV API's terms, which encourage clearing
    cached text periodically so corrections/updates propagate."""

    __tablename__ = "passage_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)
    reference: Mapped[str] = mapped_column(String, nullable=False)
    esv_text: Mapped[str] = mapped_column(Text, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (UniqueConstraint("book_id", "reference"),)


class QuizAttempt(Base):
    """The full answer key (questions_json) is persisted here and never sent
    to the client until after submission — see QuestionOut in schemas.py,
    which deliberately omits correct_index/explanation. Scoring (Phase 6)
    reads questions_json server-side to grade the client's submitted answers."""

    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)
    # Nullable: attempts created before Section existed (all generated from
    # chapter 1 only, under a since-fixed bug) have no section to point to,
    # and there's no meaningful backfill target for them.
    section_id: Mapped[int | None] = mapped_column(ForeignKey("sections.id"), nullable=True)
    chapter_reference: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="in_progress", nullable=False)
    questions_json: Mapped[list] = mapped_column(JSON, nullable=False)
    fun_facts_json: Mapped[list] = mapped_column(JSON, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # Populated only once the attempt is submitted (status -> "completed").
    answers_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class UserBookProgress(Base):
    """Per-user, per-book gamification stats — updated once per submitted
    quiz attempt (see app/services/gamification.py). Kept per-book rather
    than a single row per user so future books each track their own streak
    and mastery, the same way UserBookProgress is scoped in the plan."""

    __tablename__ = "user_book_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)
    xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    best_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quizzes_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_quiz_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "book_id"),)


class Badge(Base):
    """Static catalog seeded once by scripts/seed_badges.py — see BADGES in
    that file for the current set and their earning criteria."""

    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)


class UserBadge(Base):
    __tablename__ = "user_badges"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    badge_id: Mapped[int] = mapped_column(ForeignKey("badges.id"), nullable=False)
    earned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "badge_id"),)
