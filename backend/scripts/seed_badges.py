"""Seeds the static badge catalog. Earning criteria live in
app/services/gamification.py (BADGE_CODE constants there must match the
`code` values here) — this file only defines the catalog metadata.

Re-runnable: clears existing rows first so you can reseed after changes."""

from app import models
from app.database import Base, SessionLocal, engine

# (code, name, description)
_BADGES = [
    ("first_quiz", "First Steps", "Complete your first quiz"),
    ("perfect_score", "Perfect Score", "Answer every question correctly in a quiz"),
    ("streak_3", "3-Day Streak", "Take a quiz on 3 days in a row"),
    ("streak_7", "7-Day Streak", "Take a quiz on 7 days in a row"),
    ("quiz_master_10", "Quiz Master", "Complete 10 quizzes"),
]


def build_badges() -> list[models.Badge]:
    return [models.Badge(code=code, name=name, description=description) for code, name, description in _BADGES]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(models.Badge).delete()
        db.commit()
        db.add_all(build_badges())
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    print(f"Seeded {len(_BADGES)} badges.")
