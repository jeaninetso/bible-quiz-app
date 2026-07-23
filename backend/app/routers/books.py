from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import auth, crud, schemas
from app.database import get_db

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=list[schemas.BookOut])
def read_books(db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)):
    books = crud.list_books(db)
    sections_by_book = crud.list_sections_for_books(db, [b.id for b in books])
    return [
        schemas.BookOut(
            id=book.id,
            code=book.code,
            name=book.name,
            testament=book.testament,
            chapter_count=book.chapter_count,
            is_available=book.is_available,
            sections=[
                schemas.SectionOut(id=s.id, book_id=s.book_id, name=s.name, is_available=s.is_available)
                for s in sections_by_book[book.id]
            ],
        )
        for book in books
    ]
