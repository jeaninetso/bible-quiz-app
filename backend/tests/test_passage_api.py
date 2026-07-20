import pytest

from app import crud
from app.auth import hash_password
from app.routers import books as books_router
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


def test_passage_requires_authentication(client):
    response = client.get("/books/1/passage")
    assert response.status_code == 401


def test_passage_returns_text_for_available_book(monkeypatch, logged_in_client, db_session, seeded_books):
    monkeypatch.setattr(books_router, "fetch_passage", lambda db, book: "[1] In the days when the judges ruled...")

    ruth_book = next(b for b in crud.list_books(db_session) if b.code == "Ruth")
    response = logged_in_client.get(f"/books/{ruth_book.id}/passage")
    assert response.status_code == 200
    assert response.json() == {"reference": "Ruth", "text": "[1] In the days when the judges ruled..."}


def test_passage_404s_for_unavailable_book(logged_in_client, db_session, seeded_books):
    genesis = next(b for b in crud.list_books(db_session) if b.code == "Gen")
    response = logged_in_client.get(f"/books/{genesis.id}/passage")
    assert response.status_code == 404


def test_passage_404s_for_unknown_book(logged_in_client, seeded_books):
    response = logged_in_client.get("/books/99999/passage")
    assert response.status_code == 404


def test_passage_502s_on_esv_api_error(monkeypatch, logged_in_client, db_session, seeded_books):
    from app.services.esv_client import EsvApiError

    def raise_error(db, book):
        raise EsvApiError("ESV API returned 401: bad token")

    monkeypatch.setattr(books_router, "fetch_passage", raise_error)

    ruth_book = next(b for b in crud.list_books(db_session) if b.code == "Ruth")
    response = logged_in_client.get(f"/books/{ruth_book.id}/passage")
    assert response.status_code == 502
