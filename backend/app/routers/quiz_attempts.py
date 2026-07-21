from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import auth, crud, schemas
from app.database import get_db
from app.services import gamification
from app.utils import utcnow

router = APIRouter(prefix="/quiz-attempts", tags=["quiz-attempts"])


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

    results = []
    score = 0
    for question, selected in zip(questions, payload.answers):
        is_correct = selected is not None and selected == question["correct_index"]
        if is_correct:
            score += 1
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
