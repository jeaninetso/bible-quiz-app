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
