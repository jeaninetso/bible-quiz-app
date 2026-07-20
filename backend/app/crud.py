from sqlalchemy.orm import Session

from app import models


def get_user_by_username(db: Session, username: str) -> models.User | None:
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, username: str, password_hash: str) -> models.User:
    user = models.User(username=username, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
