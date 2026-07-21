from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import auth, crud, schemas
from app.database import get_db
from app.services.claude_quiz import ClaudeQuizError, generate_quiz
from app.services.esv_client import EsvApiError, fetch_passage

router = APIRouter(prefix="/books", tags=["quiz"])


@router.post("/{book_id}/quiz", response_model=schemas.QuizAttemptOut)
def create_quiz(
    book_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user),
):
    book = crud.get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such book")
    if not book.is_available:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{book.name} isn't available yet")

    try:
        passage_text = fetch_passage(db, book)
    except EsvApiError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    try:
        quiz = generate_quiz(passage_text, book.name)
    except ClaudeQuizError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    attempt = crud.create_quiz_attempt(
        db,
        user_id=current_user.id,
        book_id=book.id,
        chapter_reference=book.name,
        questions_json=[q.model_dump() for q in quiz.questions],
        fun_facts_json=[f.model_dump() for f in quiz.fun_facts],
    )

    return schemas.QuizAttemptOut(
        id=attempt.id,
        book_id=book.id,
        book_name=book.name,
        chapter_reference=attempt.chapter_reference,
        questions=[schemas.QuestionOut(question=q.question, options=q.options) for q in quiz.questions],
        fun_facts=[schemas.FunFactOut(fact=f.fact) for f in quiz.fun_facts],
    )
