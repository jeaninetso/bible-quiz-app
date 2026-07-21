from datetime import datetime

from sqlalchemy.orm import Session

from app import models
from app.utils import utcnow


def get_user_by_username(db: Session, username: str) -> models.User | None:
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, username: str, password_hash: str) -> models.User:
    user = models.User(username=username, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_books(db: Session) -> list[models.Book]:
    return db.query(models.Book).order_by(models.Book.order_index).all()


def get_book(db: Session, book_id: int) -> models.Book | None:
    return db.get(models.Book, book_id)


def get_cached_passage(db: Session, book_id: int, reference: str) -> models.PassageCache | None:
    cached = (
        db.query(models.PassageCache)
        .filter(models.PassageCache.book_id == book_id, models.PassageCache.reference == reference)
        .first()
    )
    if cached is not None and cached.expires_at < utcnow():
        db.delete(cached)
        db.commit()
        return None
    return cached


def upsert_passage_cache(db: Session, book_id: int, reference: str, esv_text: str, expires_at: datetime) -> None:
    existing = (
        db.query(models.PassageCache)
        .filter(models.PassageCache.book_id == book_id, models.PassageCache.reference == reference)
        .first()
    )
    if existing is not None:
        db.delete(existing)
        db.commit()
    db.add(models.PassageCache(book_id=book_id, reference=reference, esv_text=esv_text, expires_at=expires_at))
    db.commit()


def create_quiz_attempt(
    db: Session,
    user_id: int,
    book_id: int,
    chapter_reference: str,
    questions_json: list[dict],
    fun_facts_json: list[dict],
) -> models.QuizAttempt:
    attempt = models.QuizAttempt(
        user_id=user_id,
        book_id=book_id,
        chapter_reference=chapter_reference,
        questions_json=questions_json,
        fun_facts_json=fun_facts_json,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def get_quiz_attempt(db: Session, attempt_id: int) -> models.QuizAttempt | None:
    return db.get(models.QuizAttempt, attempt_id)


def submit_quiz_attempt(
    db: Session, attempt: models.QuizAttempt, answers_json: list[int | None], score: int
) -> models.QuizAttempt:
    attempt.answers_json = answers_json
    attempt.score = score
    attempt.status = "completed"
    attempt.submitted_at = utcnow()
    db.commit()
    db.refresh(attempt)
    return attempt


def list_completed_quiz_attempts(db: Session, user_id: int) -> list[models.QuizAttempt]:
    return (
        db.query(models.QuizAttempt)
        .filter(models.QuizAttempt.user_id == user_id, models.QuizAttempt.status == "completed")
        .order_by(models.QuizAttempt.submitted_at.desc())
        .all()
    )


def get_or_create_progress(db: Session, user_id: int, book_id: int) -> models.UserBookProgress:
    progress = (
        db.query(models.UserBookProgress)
        .filter(models.UserBookProgress.user_id == user_id, models.UserBookProgress.book_id == book_id)
        .first()
    )
    if progress is None:
        progress = models.UserBookProgress(user_id=user_id, book_id=book_id)
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress


def save_progress(db: Session, progress: models.UserBookProgress) -> None:
    db.commit()
    db.refresh(progress)


def list_user_progress(db: Session, user_id: int) -> list[models.UserBookProgress]:
    return db.query(models.UserBookProgress).filter(models.UserBookProgress.user_id == user_id).all()


def sum_quizzes_completed(db: Session, user_id: int) -> int:
    return sum(p.quizzes_completed for p in list_user_progress(db, user_id))


def list_badges(db: Session) -> list[models.Badge]:
    return db.query(models.Badge).all()


def get_badges_by_codes(db: Session, codes: list[str]) -> list[models.Badge]:
    if not codes:
        return []
    return db.query(models.Badge).filter(models.Badge.code.in_(codes)).all()


def list_earned_badges(db: Session, user_id: int) -> list[models.UserBadge]:
    return db.query(models.UserBadge).filter(models.UserBadge.user_id == user_id).all()


def earned_badge_codes(db: Session, user_id: int) -> set[str]:
    rows = (
        db.query(models.Badge.code)
        .join(models.UserBadge, models.UserBadge.badge_id == models.Badge.id)
        .filter(models.UserBadge.user_id == user_id)
        .all()
    )
    return {code for (code,) in rows}


def award_badges(db: Session, user_id: int, badge_codes: list[str]) -> list[models.Badge]:
    if not badge_codes:
        return []
    badges = get_badges_by_codes(db, badge_codes)
    for badge in badges:
        db.add(models.UserBadge(user_id=user_id, badge_id=badge.id))
    db.commit()
    return badges
