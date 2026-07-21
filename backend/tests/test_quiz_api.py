import pytest

from app import crud
from app.auth import hash_password
from app.routers import quiz as quiz_router
from app.services.claude_quiz import ClaudeQuizError, FunFact, QuizGenerationResult, QuizQuestion
from app.services.esv_client import EsvApiError
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


def test_quiz_requires_authentication(client):
    response = client.post("/books/1/quiz")
    assert response.status_code == 401


def test_quiz_generates_and_strips_answer_key(monkeypatch, logged_in_client, db_session, seeded_books):
    monkeypatch.setattr(quiz_router, "fetch_passage", lambda db, book: "In the days when the judges ruled...")
    monkeypatch.setattr(quiz_router, "generate_quiz", lambda passage_text, reference: _fake_quiz())

    ruth_book = next(b for b in crud.list_books(db_session) if b.code == "Ruth")
    response = logged_in_client.post(f"/books/{ruth_book.id}/quiz")
    assert response.status_code == 200

    body = response.json()
    assert body["bookName"] == "Ruth"
    assert len(body["questions"]) == 5
    assert len(body["funFacts"]) == 2
    for question in body["questions"]:
        assert set(question.keys()) == {"question", "options"}
        assert len(question["options"]) == 4


def test_quiz_persists_full_answer_key_server_side(monkeypatch, logged_in_client, db_session, seeded_books):
    monkeypatch.setattr(quiz_router, "fetch_passage", lambda db, book: "In the days when the judges ruled...")
    monkeypatch.setattr(quiz_router, "generate_quiz", lambda passage_text, reference: _fake_quiz())

    ruth_book = next(b for b in crud.list_books(db_session) if b.code == "Ruth")
    response = logged_in_client.post(f"/books/{ruth_book.id}/quiz")
    attempt_id = response.json()["id"]

    from app import models

    attempt = db_session.get(models.QuizAttempt, attempt_id)
    assert attempt is not None
    assert attempt.questions_json[0]["correct_index"] in range(4)
    assert attempt.questions_json[0]["explanation"] == "Explanation 0."


def test_quiz_404s_for_unavailable_book(logged_in_client, db_session, seeded_books):
    genesis = next(b for b in crud.list_books(db_session) if b.code == "Gen")
    response = logged_in_client.post(f"/books/{genesis.id}/quiz")
    assert response.status_code == 404


def test_quiz_404s_for_unknown_book(logged_in_client, seeded_books):
    response = logged_in_client.post("/books/99999/quiz")
    assert response.status_code == 404


def test_quiz_502s_on_esv_api_error(monkeypatch, logged_in_client, db_session, seeded_books):
    def raise_error(db, book):
        raise EsvApiError("ESV API returned 401: bad token")

    monkeypatch.setattr(quiz_router, "fetch_passage", raise_error)

    ruth_book = next(b for b in crud.list_books(db_session) if b.code == "Ruth")
    response = logged_in_client.post(f"/books/{ruth_book.id}/quiz")
    assert response.status_code == 502


def test_quiz_502s_on_claude_error(monkeypatch, logged_in_client, db_session, seeded_books):
    monkeypatch.setattr(quiz_router, "fetch_passage", lambda db, book: "In the days when the judges ruled...")

    def raise_error(passage_text, reference):
        raise ClaudeQuizError("Claude repeatedly produced invalid quiz output: malformed")

    monkeypatch.setattr(quiz_router, "generate_quiz", raise_error)

    ruth_book = next(b for b in crud.list_books(db_session) if b.code == "Ruth")
    response = logged_in_client.post(f"/books/{ruth_book.id}/quiz")
    assert response.status_code == 502
