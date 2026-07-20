import bcrypt
from fastapi import Depends, HTTPException, Request, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app import crud, models
from app.config import SESSION_SECRET
from app.database import get_db

COOKIE_NAME = "session"
SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 30  # 30 days

_serializer = URLSafeTimedSerializer(SESSION_SECRET, salt="scripture-quest-session")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_session_cookie(user_id: int) -> str:
    return _serializer.dumps({"user_id": user_id})


def _read_user_id_from_cookie(cookie_value: str) -> int | None:
    try:
        payload = _serializer.loads(cookie_value, max_age=SESSION_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    return payload.get("user_id")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    cookie_value = request.cookies.get(COOKIE_NAME)
    user_id = _read_user_id_from_cookie(cookie_value) if cookie_value else None
    user = db.get(models.User, user_id) if user_id is not None else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def authenticate_user(db: Session, username: str, password: str) -> models.User | None:
    user = crud.get_user_by_username(db, username)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user
