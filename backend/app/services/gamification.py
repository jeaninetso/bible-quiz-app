"""XP, streak, and badge logic, applied once per submitted quiz attempt.
Kept as pure-ish functions over a UserBookProgress row so the scoring math
is unit-testable without a database (see tests/test_gamification.py)."""

from datetime import date, timedelta

from app import models

XP_PER_CORRECT_ANSWER = 10
XP_COMPLETION_BONUS = 20
XP_PER_LEVEL = 100

# Must match the `code` column seeded by scripts/seed_badges.py.
FIRST_QUIZ = "first_quiz"
PERFECT_SCORE = "perfect_score"
STREAK_3 = "streak_3"
STREAK_7 = "streak_7"
QUIZ_MASTER_10 = "quiz_master_10"


def compute_xp_earned(score: int) -> int:
    return XP_COMPLETION_BONUS + score * XP_PER_CORRECT_ANSWER


def compute_level(total_xp: int) -> int:
    return total_xp // XP_PER_LEVEL + 1


def apply_quiz_result(
    progress: models.UserBookProgress, score: int, total_questions: int, today: date
) -> int:
    """Mutates `progress` in place for one freshly-submitted attempt on its
    book. Returns the XP earned by this attempt (not the new total)."""
    if progress.last_quiz_date == today:
        pass  # already took a quiz today — streak unchanged, don't double-count
    elif progress.last_quiz_date == today - timedelta(days=1):
        progress.current_streak += 1
    else:
        progress.current_streak = 1
    progress.longest_streak = max(progress.longest_streak, progress.current_streak)
    progress.last_quiz_date = today

    xp_earned = compute_xp_earned(score)
    progress.xp += xp_earned
    progress.level = compute_level(progress.xp)
    progress.best_score = max(progress.best_score, score)
    progress.quizzes_completed += 1

    return xp_earned


def determine_new_badge_codes(
    already_earned: set[str],
    progress: models.UserBookProgress,
    score: int,
    total_questions: int,
    total_quizzes_across_books: int,
) -> list[str]:
    """Badge criteria. first_quiz/quiz_master_10 look at the user's total
    quizzes across all books (global milestones); the streak badges look at
    this book's streak, since cross-book streak semantics aren't defined yet
    while only one book is available."""
    earned_now = []

    def award(code: str, condition: bool) -> None:
        if condition and code not in already_earned:
            earned_now.append(code)

    award(FIRST_QUIZ, total_quizzes_across_books == 1)
    award(PERFECT_SCORE, total_questions > 0 and score == total_questions)
    award(STREAK_3, progress.current_streak >= 3)
    award(STREAK_7, progress.current_streak >= 7)
    award(QUIZ_MASTER_10, total_quizzes_across_books >= 10)

    return earned_now
