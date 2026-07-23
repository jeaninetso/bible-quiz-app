from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import auth, crud, schemas
from app.database import get_db
from app.services.claude_quiz import ClaudeQuizError, generate_quiz
from app.services.esv_client import EsvApiError, fetch_passage

router = APIRouter(prefix="/sections", tags=["quiz"])


@router.post("/{section_id}/quiz", response_model=schemas.QuizAttemptOut)
def create_quiz(
    section_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user),
):
    section = crud.get_section(db, section_id)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such section")
    if not section.is_available:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{section.name} isn't available yet")

    book = crud.get_book(db, section.book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such book")

    try:
        passage_text = fetch_passage(db, book, reference=section.reference)
    except EsvApiError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    try:
        quiz = generate_quiz(passage_text, section.reference)
    except ClaudeQuizError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    attempt = crud.create_quiz_attempt(
        db,
        user_id=current_user.id,
        book_id=book.id,
        section_id=section.id,
        chapter_reference=section.reference,
        questions_json=[q.model_dump() for q in quiz.questions],
        fun_facts_json=[f.model_dump() for f in quiz.fun_facts],
    )

    return schemas.QuizAttemptOut(
        id=attempt.id,
        book_id=book.id,
        book_name=book.name,
        section_id=section.id,
        section_name=section.name,
        chapter_reference=attempt.chapter_reference,
        questions=[schemas.QuestionOut(question=q.question, options=q.options) for q in quiz.questions],
        fun_facts=[schemas.FunFactOut(fact=f.fact) for f in quiz.fun_facts],
    )
