import pytest

from app import crud
from app.auth import hash_password


@pytest.fixture()
def seeded_user(db_session):
    return crud.create_user(db_session, "jeanine", hash_password("correct-horse"))


def test_login_success_sets_cookie_and_returns_username(client, seeded_user):
    response = client.post("/auth/login", json={"username": "jeanine", "password": "correct-horse"})
    assert response.status_code == 200
    assert response.json() == {"username": "jeanine"}
    assert "session" in response.cookies


def test_login_wrong_password_rejected(client, seeded_user):
    response = client.post("/auth/login", json={"username": "jeanine", "password": "wrong"})
    assert response.status_code == 401


def test_login_unknown_username_rejected(client):
    response = client.post("/auth/login", json={"username": "ghost", "password": "whatever"})
    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user_after_login(client, seeded_user):
    client.post("/auth/login", json={"username": "jeanine", "password": "correct-horse"})
    response = client.get("/auth/me")
    assert response.status_code == 200
    assert response.json() == {"username": "jeanine"}


def test_logout_clears_session(client, seeded_user):
    client.post("/auth/login", json={"username": "jeanine", "password": "correct-horse"})
    client.post("/auth/logout")
    response = client.get("/auth/me")
    assert response.status_code == 401
