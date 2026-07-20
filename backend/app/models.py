"""SQLAlchemy models. UserBookProgress/QuizAttempt/Badge arrive in
Phases 6 and 7."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
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
