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


def test_stats_requires_authentication(client):
    response = client.get("/me/stats")
    assert response.status_code == 401


def test_stats_are_zero_before_any_quiz(logged_in_client):
    response = logged_in_client.get("/me/stats")
    assert response.status_code == 200
    assert response.json() == {
        "totalXp": 0,
        "level": 1,
        "currentStreak": 0,
        "longestStreak": 0,
        "quizzesCompleted": 0,
        "badges": [],
    }


def test_stats_reflect_submitted_quizzes_and_earned_badges(
    monkeypatch, logged_in_client, db_session, seeded_books, seeded_badges
):
    monkeypatch.setattr(quiz_router, "fetch_passage", lambda db, book: "In the days when the judges ruled...")
    monkeypatch.setattr(quiz_router, "generate_quiz", lambda passage_text, reference: _fake_quiz())
    monkeypatch.setattr(quiz_attempts_router, "utcnow", lambda: datetime(2026, 1, 10))

    ruth_book = next(b for b in crud.list_books(db_session) if b.code == "Ruth")
    attempt_id = logged_in_client.post(f"/books/{ruth_book.id}/quiz").json()["id"]
    logged_in_client.post(f"/quiz-attempts/{attempt_id}/submit", json={"answers": [0, 1, 2, 3, 0]})

    response = logged_in_client.get("/me/stats")
    assert response.status_code == 200
    body = response.json()

    assert body["totalXp"] == 70
    assert body["level"] == 1
    assert body["currentStreak"] == 1
    assert body["longestStreak"] == 1
    assert body["quizzesCompleted"] == 1
    assert {b["code"] for b in body["badges"]} == {"first_quiz", "perfect_score"}
    assert all("earnedAt" in b for b in body["badges"])
