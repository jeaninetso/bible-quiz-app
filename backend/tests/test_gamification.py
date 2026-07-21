from datetime import date

from app import models
from app.services import gamification


def _progress(**overrides) -> models.UserBookProgress:
    defaults = dict(
        user_id=1,
        book_id=1,
        xp=0,
        level=1,
        current_streak=0,
        longest_streak=0,
        best_score=0,
        quizzes_completed=0,
        last_quiz_date=None,
    )
    defaults.update(overrides)
    return models.UserBookProgress(**defaults)


def test_compute_xp_earned_includes_completion_bonus_and_per_correct_answer():
    assert gamification.compute_xp_earned(0) == gamification.XP_COMPLETION_BONUS
    assert gamification.compute_xp_earned(5) == gamification.XP_COMPLETION_BONUS + 5 * gamification.XP_PER_CORRECT_ANSWER


def test_compute_level_scales_with_xp():
    assert gamification.compute_level(0) == 1
    assert gamification.compute_level(99) == 1
    assert gamification.compute_level(100) == 2
    assert gamification.compute_level(250) == 3


def test_apply_quiz_result_starts_a_streak_on_first_attempt():
    progress = _progress()
    today = date(2026, 1, 10)

    xp_earned = gamification.apply_quiz_result(progress, score=3, total_questions=5, today=today)

    assert xp_earned == gamification.XP_COMPLETION_BONUS + 3 * gamification.XP_PER_CORRECT_ANSWER
    assert progress.xp == xp_earned
    assert progress.current_streak == 1
    assert progress.longest_streak == 1
    assert progress.best_score == 3
    assert progress.quizzes_completed == 1
    assert progress.last_quiz_date == today


def test_apply_quiz_result_extends_streak_on_consecutive_day():
    progress = _progress(current_streak=2, longest_streak=2, last_quiz_date=date(2026, 1, 10))

    gamification.apply_quiz_result(progress, score=1, total_questions=5, today=date(2026, 1, 11))

    assert progress.current_streak == 3
    assert progress.longest_streak == 3


def test_apply_quiz_result_does_not_double_count_same_day():
    progress = _progress(current_streak=2, longest_streak=2, last_quiz_date=date(2026, 1, 10))

    gamification.apply_quiz_result(progress, score=1, total_questions=5, today=date(2026, 1, 10))

    assert progress.current_streak == 2
    assert progress.quizzes_completed == 1  # still counted as a completed quiz


def test_apply_quiz_result_resets_streak_after_a_gap():
    progress = _progress(current_streak=5, longest_streak=5, last_quiz_date=date(2026, 1, 10))

    gamification.apply_quiz_result(progress, score=1, total_questions=5, today=date(2026, 1, 13))

    assert progress.current_streak == 1
    assert progress.longest_streak == 5  # longest streak is never reduced


def test_apply_quiz_result_tracks_best_score_across_attempts():
    progress = _progress(best_score=2)
    gamification.apply_quiz_result(progress, score=1, total_questions=5, today=date(2026, 1, 10))
    assert progress.best_score == 2  # unchanged — 1 < 2

    gamification.apply_quiz_result(progress, score=4, total_questions=5, today=date(2026, 1, 11))
    assert progress.best_score == 4


def test_determine_new_badge_codes_awards_first_quiz_and_perfect_score():
    progress = _progress(current_streak=1)
    new = gamification.determine_new_badge_codes(
        already_earned=set(), progress=progress, score=5, total_questions=5, total_quizzes_across_books=1
    )
    assert set(new) == {gamification.FIRST_QUIZ, gamification.PERFECT_SCORE}


def test_determine_new_badge_codes_skips_already_earned():
    progress = _progress(current_streak=1)
    new = gamification.determine_new_badge_codes(
        already_earned={gamification.FIRST_QUIZ},
        progress=progress,
        score=5,
        total_questions=5,
        total_quizzes_across_books=1,
    )
    assert gamification.FIRST_QUIZ not in new
    assert gamification.PERFECT_SCORE in new


def test_determine_new_badge_codes_awards_streak_badges():
    progress = _progress(current_streak=7)
    new = gamification.determine_new_badge_codes(
        already_earned=set(), progress=progress, score=2, total_questions=5, total_quizzes_across_books=7
    )
    assert gamification.STREAK_3 in new
    assert gamification.STREAK_7 in new
    assert gamification.PERFECT_SCORE not in new


def test_determine_new_badge_codes_awards_quiz_master_at_ten():
    progress = _progress(current_streak=1)
    new = gamification.determine_new_badge_codes(
        already_earned=set(), progress=progress, score=1, total_questions=5, total_quizzes_across_books=10
    )
    assert gamification.QUIZ_MASTER_10 in new
