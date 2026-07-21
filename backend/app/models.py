"""SQLAlchemy models. UserBookProgress/Badge arrive in Phases 6 and 7."""

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
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
    chapter_reference: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="in_progress", nullable=False)
    questions_json: Mapped[list] = mapped_column(JSON, nullable=False)
    fun_facts_json: Mapped[list] = mapped_column(JSON, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
