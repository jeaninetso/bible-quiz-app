from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import auth, crud, schemas
from app.database import get_db
from app.services.gamification import compute_level

router = APIRouter(tags=["stats"])


@router.get("/me/stats", response_model=schemas.MeStatsOut)
def read_my_stats(db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)):
    progress_rows = crud.list_user_progress(db, current_user.id)
    total_xp = sum(p.xp for p in progress_rows)
    current_streak = max((p.current_streak for p in progress_rows), default=0)
    longest_streak = max((p.longest_streak for p in progress_rows), default=0)
    quizzes_completed = sum(p.quizzes_completed for p in progress_rows)

    badge_rows = crud.list_earned_badges(db, current_user.id)
    badges_by_id = {b.id: b for b in crud.list_badges(db)}
    badges = [
        schemas.EarnedBadgeOut(
            code=badges_by_id[ub.badge_id].code,
            name=badges_by_id[ub.badge_id].name,
            description=badges_by_id[ub.badge_id].description,
            earned_at=ub.earned_at,
        )
        for ub in badge_rows
        if ub.badge_id in badges_by_id
    ]

    return schemas.MeStatsOut(
        total_xp=total_xp,
        level=compute_level(total_xp),
        current_streak=current_streak,
        longest_streak=longest_streak,
        quizzes_completed=quizzes_completed,
        badges=badges,
    )
