from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app import auth, schemas
from app.config import COOKIE_SECURE
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.UserOut)
def login(body: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, body.username, body.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    response.set_cookie(
        key=auth.COOKIE_NAME,
        value=auth.create_session_cookie(user.id),
        max_age=auth.SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
    )
    return user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(auth.COOKIE_NAME)
    return {"status": "logged_out"}


@router.get("/me", response_model=schemas.UserOut)
def me(current_user=Depends(auth.get_current_user)):
    return current_user
