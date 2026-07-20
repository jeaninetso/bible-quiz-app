import pytest

from app import crud
from app.auth import hash_password
from scripts.seed_books import build_books


@pytest.fixture()
def logged_in_client(client, db_session):
    crud.create_user(db_session, "jeanine", hash_password("correct-horse"))
    client.post("/auth/login", json={"username": "jeanine", "password": "correct-horse"})
    return client


def test_books_requires_authentication(client):
    response = client.get("/books")
    assert response.status_code == 401


def test_books_returns_all_66_in_canonical_order(logged_in_client, db_session):
    db_session.add_all(build_books())
    db_session.commit()

    response = logged_in_client.get("/books")
    assert response.status_code == 200
    books = response.json()

    assert len(books) == 66
    assert books[0]["name"] == "Genesis"
    assert books[38]["name"] == "Malachi"
    assert books[39]["name"] == "Matthew"
    assert books[-1]["name"] == "Revelation"


def test_only_ruth_is_available(logged_in_client, db_session):
    db_session.add_all(build_books())
    db_session.commit()

    books = logged_in_client.get("/books").json()
    available = [b["name"] for b in books if b["isAvailable"]]
    assert available == ["Ruth"]
