from datetime import datetime

import pytest

from app import crud
from app.auth import hash_password
from app.routers import quiz as quiz_router
from app.routers import quiz_attempts as quiz_attempts_router
from app.services.claude_quiz import FunFact, QuizGenerationResult, QuizQuestion
from scripts.seed_badges import build_badges
from scripts.seed_books import build_books


@pytest.fixture()
def logged_in_client(client, db_session):
    crud.create_user(db_session, "jeanine", hash_password("correct-horse"))
    client.post("/auth/login", json={"username": "jeanine", "password": "correct-horse"})
    return client


@pytest.fixture()
def seeded_books(db_session):
    db_session.add_all(build_books())
    db_session.commit()


@pytest.fixture()
def seeded_badges(db_session):
    db_session.add_all(build_badges())
    db_session.commit()


def _fake_quiz():
    # correct_index cycles 0,1,2,3,0 — deterministic answer key for tests.
    return QuizGenerationResult(
        questions=[
            QuizQuestion(
                question=f"Sample question {i}?",
                options=["A", "B", "C", "D"],
                correct_index=i % 4,
                explanation=f"Explanation {i}.",
            )
            for i in range(5)
        ],
        fun_facts=[FunFact(fact="Ruth's story sets up the lineage of King David."), FunFact(fact="Ruth was a Moabite.")],
    )


@pytest.fixture()
def quiz_attempt_id(monkeypatch, logged_in_client, db_session, seeded_books):
    monkeypatch.setattr(quiz_router, "fetch_passage", lambda db, book: "In the days when the judges ruled...")
    monkeypatch.setattr(quiz_router, "generate_quiz", lambda passage_text, reference: _fake_quiz())

    ruth_book = next(b for b in crud.list_books(db_session) if b.code == "Ruth")
    response = logged_in_client.post(f"/books/{ruth_book.id}/quiz")
    return response.json()["id"]


def test_submit_requires_authentication(client, quiz_attempt_id):
    # quiz_attempt_id's setup logs the shared TestClient in as "jeanine" —
    # clear that session cookie to actually exercise the unauthenticated path.
    client.cookies.clear()
    response = client.post(f"/quiz-attempts/{quiz_attempt_id}/submit", json={"answers": [0, 1, 2, 3, 0]})
    assert response.status_code == 401


def test_submit_scores_correctly_and_reveals_answer_key(logged_in_client, quiz_attempt_id):
    # Matches the answer key exactly (0,1,2,3,0) -> perfect score.
    response = logged_in_client.post(f"/quiz-attempts/{quiz_attempt_id}/submit", json={"answers": [0, 1, 2, 3, 0]})
    assert response.status_code == 200

    body = response.json()
    assert body["score"] == 5
    assert body["totalQuestions"] == 5
    for question in body["questions"]:
        assert question["isCorrect"] is True
        assert "correctIndex" in question
        assert "explanation" in question


def test_submit_scores_partial_and_unanswered_correctly(logged_in_client, quiz_attempt_id):
    # Q1 wrong (1 vs correct 0), Q2 correct (1), Q3 unanswered (None), Q4 correct (3), Q5 wrong (1 vs 0).
    response = logged_in_client.post(
        f"/quiz-attempts/{quiz_attempt_id}/submit", json={"answers": [1, 1, None, 3, 1]}
    )
    assert response.status_code == 200

    body = response.json()
    assert body["score"] == 2
    results = body["questions"]
    assert [r["isCorrect"] for r in results] == [False, True, False, True, False]
    assert results[2]["selectedIndex"] is None


def test_submit_rejects_wrong_answer_count(logged_in_client, quiz_attempt_id):
    response = logged_in_client.post(f"/quiz-attempts/{quiz_attempt_id}/submit", json={"answers": [0, 1]})
    assert response.status_code == 400


def test_submit_rejects_resubmission(logged_in_client, quiz_attempt_id):
    first = logged_in_client.post(f"/quiz-attempts/{quiz_attempt_id}/submit", json={"answers": [0, 1, 2, 3, 0]})
    assert first.status_code == 200

    second = logged_in_client.post(f"/quiz-attempts/{quiz_attempt_id}/submit", json={"answers": [0, 1, 2, 3, 0]})
    assert second.status_code == 409


def test_submit_404s_for_unknown_attempt(logged_in_client):
    response = logged_in_client.post("/quiz-attempts/99999/submit", json={"answers": []})
    assert response.status_code == 404


def test_submit_404s_for_another_users_attempt(client, db_session, quiz_attempt_id):
    crud.create_user(db_session, "other_user", hash_password("other-pw-123"))
    client.post("/auth/login", json={"username": "other_user", "password": "other-pw-123"})

    response = client.post(f"/quiz-attempts/{quiz_attempt_id}/submit", json={"answers": [0, 1, 2, 3, 0]})
    assert response.status_code == 404


def test_submit_persists_score_and_completed_status(logged_in_client, db_session, quiz_attempt_id):
    logged_in_client.post(f"/quiz-attempts/{quiz_attempt_id}/submit", json={"answers": [0, 1, 2, 3, 0]})

    from app import models

    attempt = db_session.get(models.QuizAttempt, quiz_attempt_id)
    assert attempt.status == "completed"
    assert attempt.score == 5
    assert attempt.answers_json == [0, 1, 2, 3, 0]
    assert attempt.submitted_at is not None


def _create_attempt(client, book_id) -> int:
    return client.post(f"/books/{book_id}/quiz").json()["id"]


def test_submit_response_includes_xp_progress_and_new_badges(
    monkeypatch, logged_in_client, db_session, seeded_books, seeded_badges
):
    monkeypatch.setattr(quiz_router, "fetch_passage", lambda db, book: "In the days when the judges ruled...")
    monkeypatch.setattr(quiz_router, "generate_quiz", lambda passage_text, reference: _fake_quiz())
    monkeypatch.setattr(quiz_attempts_router, "utcnow", lambda: datetime(2026, 1, 10))

    ruth_book = next(b for b in crud.list_books(db_session) if b.code == "Ruth")
    attempt_id = _create_attempt(logged_in_client, ruth_book.id)

    response = logged_in_client.post(f"/quiz-attempts/{attempt_id}/submit", json={"answers": [0, 1, 2, 3, 0]})
    assert response.status_code == 200
    body = response.json()

    assert body["xpEarned"] == 20 + 5 * 10  # completion bonus + 5 correct answers
    progress = body["progress"]
    assert progress == {
        "xp": 70,
        "level": 1,
        "currentStreak": 1,
        "longestStreak": 1,
        "bestScore": 5,
        "quizzesCompleted": 1,
    }
    assert {b["code"] for b in body["newBadges"]} == {"first_quiz", "perfect_score"}
    assert all({"code", "name", "description"} <= set(b.keys()) for b in body["newBadges"])


def test_submit_does_not_reaward_badges_already_earned(
    monkeypatch, logged_in_client, db_session, seeded_books, seeded_badges
):
    monkeypatch.setattr(quiz_router, "fetch_passage", lambda db, book: "In the days when the judges ruled...")
    monkeypatch.setattr(quiz_router, "generate_quiz", lambda passage_text, reference: _fake_quiz())
    monkeypatch.setattr(quiz_attempts_router, "utcnow", lambda: datetime(2026, 1, 10))

    ruth_book = next(b for b in crud.list_books(db_session) if b.code == "Ruth")

    first_id = _create_attempt(logged_in_client, ruth_book.id)
    logged_in_client.post(f"/quiz-attempts/{first_id}/submit", json={"answers": [0, 1, 2, 3, 0]})

    second_id = _create_attempt(logged_in_client, ruth_book.id)
    response = logged_in_client.post(f"/quiz-attempts/{second_id}/submit", json={"answers": [0, 1, 2, 3, 0]})

    assert response.json()["newBadges"] == []


def test_submit_builds_streak_across_consecutive_days_and_awards_streak_badge(
    monkeypatch, logged_in_client, db_session, seeded_books, seeded_badges
):
    monkeypatch.setattr(quiz_router, "fetch_passage", lambda db, book: "In the days when the judges ruled...")
    monkeypatch.setattr(quiz_router, "generate_quiz", lambda passage_text, reference: _fake_quiz())

    ruth_book = next(b for b in crud.list_books(db_session) if b.code == "Ruth")

    body = None
    for day in (10, 11, 12):
        monkeypatch.setattr(quiz_attempts_router, "utcnow", lambda day=day: datetime(2026, 1, day))
        attempt_id = _create_attempt(logged_in_client, ruth_book.id)
        response = logged_in_client.post(f"/quiz-attempts/{attempt_id}/submit", json={"answers": [0, 1, 2, 3, 0]})
        body = response.json()

    assert body["progress"]["currentStreak"] == 3
    assert body["progress"]["quizzesCompleted"] == 3
    assert "streak_3" in {b["code"] for b in body["newBadges"]}


def test_submit_persists_user_book_progress_row(monkeypatch, logged_in_client, db_session, seeded_books, seeded_badges):
    monkeypatch.setattr(quiz_router, "fetch_passage", lambda db, book: "In the days when the judges ruled...")
    monkeypatch.setattr(quiz_router, "generate_quiz", lambda passage_text, reference: _fake_quiz())
    monkeypatch.setattr(quiz_attempts_router, "utcnow", lambda: datetime(2026, 1, 10))

    ruth_book = next(b for b in crud.list_books(db_session) if b.code == "Ruth")
    attempt_id = _create_attempt(logged_in_client, ruth_book.id)
    logged_in_client.post(f"/quiz-attempts/{attempt_id}/submit", json={"answers": [0, 1, 2, 3, 0]})

    from app import models

    progress = (
        db_session.query(models.UserBookProgress)
        .filter(models.UserBookProgress.book_id == ruth_book.id)
        .first()
    )
    assert progress is not None
    assert progress.xp == 70
    assert progress.last_quiz_date == datetime(2026, 1, 10).date()
