from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import auth, crud, schemas
from app.database import get_db

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=list[schemas.BookOut])
def read_books(db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)):
    return crud.list_books(db)
