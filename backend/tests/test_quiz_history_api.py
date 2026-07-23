import pytest

from app import crud
from app.auth import hash_password
from app.routers import quiz as quiz_router
from app.services.claude_quiz import FunFact, QuizGenerationResult, QuizQuestion
from scripts.seed_books import build_books
from scripts.seed_sections import build_sections


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
def seeded_sections(db_session, seeded_books):
    db_session.add_all(build_sections(db_session))
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


@pytest.fixture()
def ruth_section_id(db_session, seeded_sections):
    ruth_book = next(b for b in crud.list_books(db_session) if b.code == "Ruth")
    return crud.list_sections_for_book(db_session, ruth_book.id)[0].id


def _create_attempt(monkeypatch, client, section_id) -> int:
    monkeypatch.setattr(quiz_router, "fetch_passage", lambda db, book, reference: "In the days when the judges ruled...")
    monkeypatch.setattr(quiz_router, "generate_quiz", lambda passage_text, reference: _fake_quiz())
    return client.post(f"/sections/{section_id}/quiz").json()["id"]


def test_history_requires_authentication(client):
    response = client.get("/quiz-attempts")
    assert response.status_code == 401


def test_history_is_empty_before_any_submission(logged_in_client):
    response = logged_in_client.get("/quiz-attempts")
    assert response.status_code == 200
    assert response.json() == []


def test_history_excludes_in_progress_attempts(monkeypatch, logged_in_client, ruth_section_id):
    _create_attempt(monkeypatch, logged_in_client, ruth_section_id)

    response = logged_in_client.get("/quiz-attempts")
    assert response.status_code == 200
    assert response.json() == []


def test_history_groups_retakes_of_the_same_section(monkeypatch, logged_in_client, ruth_section_id):
    first_id = _create_attempt(monkeypatch, logged_in_client, ruth_section_id)
    logged_in_client.post(f"/quiz-attempts/{first_id}/submit", json={"answers": [0, 1, 2, 3, 0]})

    second_id = _create_attempt(monkeypatch, logged_in_client, ruth_section_id)
    logged_in_client.post(f"/quiz-attempts/{second_id}/submit", json={"answers": [1, 1, 1, 1, 1]})

    response = logged_in_client.get("/quiz-attempts")
    assert response.status_code == 200
    body = response.json()

    assert len(body) == 1  # one group, not two flat rows
    group = body[0]
    assert group["bookName"] == "Ruth"
    assert group["sectionName"] == "Ruth 1–2"
    assert group["attemptCount"] == 2
    assert group["mostRecentScore"] == 1  # only index 1 matches correct_index 1 -> the second, most recent attempt
    assert group["mostRecentTotalQuestions"] == 5
    assert "mostRecentSubmittedAt" in group
    assert [a["id"] for a in group["attempts"]] == [second_id, first_id]  # newest first
    assert [a["score"] for a in group["attempts"]] == [1, 5]


def test_history_lists_different_sections_as_separate_groups_newest_first(
    monkeypatch, logged_in_client, db_session, seeded_sections
):
    ruth_book = next(b for b in crud.list_books(db_session) if b.code == "Ruth")
    ruth_sections = crud.list_sections_for_book(db_session, ruth_book.id)

    first_id = _create_attempt(monkeypatch, logged_in_client, ruth_sections[0].id)
    logged_in_client.post(f"/quiz-attempts/{first_id}/submit", json={"answers": [0, 1, 2, 3, 0]})

    second_id = _create_attempt(monkeypatch, logged_in_client, ruth_sections[1].id)
    logged_in_client.post(f"/quiz-attempts/{second_id}/submit", json={"answers": [0, 1, 2, 3, 0]})

    response = logged_in_client.get("/quiz-attempts")
    body = response.json()

    assert len(body) == 2
    assert [g["sectionName"] for g in body] == ["Ruth 3–4", "Ruth 1–2"]
    assert all(g["attemptCount"] == 1 for g in body)


def test_history_only_shows_the_current_users_attempts(monkeypatch, logged_in_client, db_session, ruth_section_id):
    attempt_id = _create_attempt(monkeypatch, logged_in_client, ruth_section_id)
    logged_in_client.post(f"/quiz-attempts/{attempt_id}/submit", json={"answers": [0, 1, 2, 3, 0]})

    crud.create_user(db_session, "other_user", hash_password("other-pw-123"))
    logged_in_client.post("/auth/login", json={"username": "other_user", "password": "other-pw-123"})

    response = logged_in_client.get("/quiz-attempts")
    assert response.status_code == 200
    assert response.json() == []


def test_review_requires_authentication(client):
    response = client.get("/quiz-attempts/1")
    assert response.status_code == 401


def test_review_returns_full_answer_key_for_a_completed_attempt(monkeypatch, logged_in_client, ruth_section_id):
    attempt_id = _create_attempt(monkeypatch, logged_in_client, ruth_section_id)
    logged_in_client.post(f"/quiz-attempts/{attempt_id}/submit", json={"answers": [0, 1, 2, 3, 0]})

    response = logged_in_client.get(f"/quiz-attempts/{attempt_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["bookName"] == "Ruth"
    assert body["sectionName"] == "Ruth 1–2"
    assert body["score"] == 5
    assert body["totalQuestions"] == 5
    assert len(body["questions"]) == 5
    for q in body["questions"]:
        assert q["isCorrect"] is True
        assert "correctIndex" in q
        assert "explanation" in q


def test_review_409s_for_an_unsubmitted_attempt(monkeypatch, logged_in_client, ruth_section_id):
    attempt_id = _create_attempt(monkeypatch, logged_in_client, ruth_section_id)

    response = logged_in_client.get(f"/quiz-attempts/{attempt_id}")
    assert response.status_code == 409


def test_review_404s_for_unknown_attempt(logged_in_client):
    response = logged_in_client.get("/quiz-attempts/99999")
    assert response.status_code == 404


def test_review_404s_for_another_users_attempt(monkeypatch, logged_in_client, db_session, ruth_section_id):
    attempt_id = _create_attempt(monkeypatch, logged_in_client, ruth_section_id)
    logged_in_client.post(f"/quiz-attempts/{attempt_id}/submit", json={"answers": [0, 1, 2, 3, 0]})

    crud.create_user(db_session, "other_user", hash_password("other-pw-123"))
    logged_in_client.post("/auth/login", json={"username": "other_user", "password": "other-pw-123"})

    response = logged_in_client.get(f"/quiz-attempts/{attempt_id}")
    assert response.status_code == 404
