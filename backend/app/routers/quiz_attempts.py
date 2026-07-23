from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import auth, crud, schemas
from app.database import get_db
from app.services import gamification
from app.utils import utcnow

router = APIRouter(prefix="/quiz-attempts", tags=["quiz-attempts"])


def _build_question_results(
    questions_json: list[dict], answers_json: list[int | None]
) -> list[schemas.QuestionResultOut]:
    results = []
    for question, selected in zip(questions_json, answers_json):
        is_correct = selected is not None and selected == question["correct_index"]
        results.append(
            schemas.QuestionResultOut(
                question=question["question"],
                options=question["options"],
                correct_index=question["correct_index"],
                explanation=question["explanation"],
                selected_index=selected,
                is_correct=is_correct,
            )
        )
    return results


@router.get("", response_model=list[schemas.QuizHistoryGroupOut])
def list_quiz_history(db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)):
    # Newest-first from crud — that ordering is reused below both to sort
    # groups (by their most-recently-seen attempt) and to sort attempts
    # within each group, with no extra sort step needed.
    attempts = crud.list_completed_quiz_attempts(db, current_user.id)
    books_by_id = {b.id: b for b in crud.list_books(db)}
    sections_by_id = crud.get_sections_by_ids(db, [a.section_id for a in attempts])

    grouped: dict[tuple[int, int | None], list] = {}
    group_order: list[tuple[int, int | None]] = []
    for attempt in attempts:
        key = (attempt.book_id, attempt.section_id)
        if key not in grouped:
            grouped[key] = []
            group_order.append(key)
        grouped[key].append(attempt)

    result = []
    for book_id, section_id in group_order:
        group_attempts = grouped[(book_id, section_id)]
        most_recent = group_attempts[0]
        book = books_by_id.get(book_id)
        section = sections_by_id.get(section_id) if section_id is not None else None
        result.append(
            schemas.QuizHistoryGroupOut(
                book_id=book_id,
                book_name=book.name if book else most_recent.chapter_reference,
                section_id=section_id,
                section_name=section.name if section else None,
                attempt_count=len(group_attempts),
                most_recent_score=most_recent.score,
                most_recent_total_questions=len(most_recent.questions_json),
                most_recent_submitted_at=most_recent.submitted_at,
                attempts=[
                    schemas.QuizHistoryAttemptOut(
                        id=a.id,
                        score=a.score,
                        total_questions=len(a.questions_json),
                        submitted_at=a.submitted_at,
                    )
                    for a in group_attempts
                ],
            )
        )
    return result


@router.get("/{attempt_id}", response_model=schemas.QuizReviewOut)
def get_quiz_review(attempt_id: int, db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)):
    attempt = crud.get_quiz_attempt(db, attempt_id)
    if attempt is None or attempt.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such quiz attempt")
    if attempt.status != "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This quiz attempt hasn't been submitted yet")

    book = crud.get_book(db, attempt.book_id)
    section = crud.get_section(db, attempt.section_id) if attempt.section_id is not None else None
    return schemas.QuizReviewOut(
        id=attempt.id,
        book_name=book.name if book else attempt.chapter_reference,
        section_id=attempt.section_id,
        section_name=section.name if section else None,
        chapter_reference=attempt.chapter_reference,
        score=attempt.score,
        total_questions=len(attempt.questions_json),
        submitted_at=attempt.submitted_at,
        questions=_build_question_results(attempt.questions_json, attempt.answers_json),
    )


@router.post("/{attempt_id}/submit", response_model=schemas.QuizResultOut)
def submit_quiz(
    attempt_id: int,
    payload: schemas.SubmitQuizRequest,
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user),
):
    attempt = crud.get_quiz_attempt(db, attempt_id)
    # 404 (not 403) for someone else's attempt too — don't reveal it exists.
    if attempt is None or attempt.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such quiz attempt")
    if attempt.status == "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This quiz attempt was already submitted")

    questions = attempt.questions_json
    if len(payload.answers) != len(questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected {len(questions)} answers, got {len(payload.answers)}",
        )

    results = _build_question_results(questions, payload.answers)
    score = sum(1 for r in results if r.is_correct)

    crud.submit_quiz_attempt(db, attempt, payload.answers, score)

    progress = crud.get_or_create_progress(db, current_user.id, attempt.book_id)
    xp_earned = gamification.apply_quiz_result(progress, score, len(questions), utcnow().date())
    crud.save_progress(db, progress)

    already_earned = crud.earned_badge_codes(db, current_user.id)
    total_quizzes = crud.sum_quizzes_completed(db, current_user.id)
    new_badge_codes = gamification.determine_new_badge_codes(
        already_earned, progress, score, len(questions), total_quizzes
    )
    new_badges = crud.award_badges(db, current_user.id, new_badge_codes)

    return schemas.QuizResultOut(
        id=attempt.id,
        score=score,
        total_questions=len(questions),
        questions=results,
        xp_earned=xp_earned,
        progress=schemas.UserBookProgressOut(
            xp=progress.xp,
            level=progress.level,
            current_streak=progress.current_streak,
            longest_streak=progress.longest_streak,
            best_score=progress.best_score,
            quizzes_completed=progress.quizzes_completed,
        ),
        new_badges=[schemas.BadgeOut(code=b.code, name=b.name, description=b.description) for b in new_badges],
    )
