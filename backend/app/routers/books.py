from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import auth, crud, schemas
from app.database import get_db
from app.services.esv_client import EsvApiError, fetch_passage

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=list[schemas.BookOut])
def read_books(db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)):
    return crud.list_books(db)


@router.get("/{book_id}/passage", response_model=schemas.PassageOut)
def read_passage(book_id: int, db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)):
    book = crud.get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such book")
    if not book.is_available:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{book.name} isn't available yet")

    try:
        text = fetch_passage(db, book)
    except EsvApiError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return schemas.PassageOut(reference=book.name, text=text)
