from datetime import timedelta

import httpx
import pytest

from app import crud, models
from app.services import esv_client
from app.utils import utcnow


@pytest.fixture()
def ruth(db_session):
    book = models.Book(code="Ruth", name="Ruth", testament="old", chapter_count=4, order_index=7, is_available=True)
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)
    return book


def _fake_esv_response(text: str):
    return httpx.Response(200, json={"passages": [text]})


def test_fetch_passage_calls_esv_api_and_caches(monkeypatch, db_session, ruth):
    monkeypatch.setattr(esv_client, "ESV_API_KEY", "fake-key")
    calls = []

    def fake_get(url, params, headers, timeout):
        calls.append(params["q"])
        return _fake_esv_response("[1] In the days... (ESV)")

    monkeypatch.setattr(esv_client.httpx, "get", fake_get)

    text = esv_client.fetch_passage(db_session, ruth)
    assert "In the days" in text
    assert calls == ["Ruth 1-4"]

    # Second call within the TTL should hit the cache, not the API again.
    esv_client.fetch_passage(db_session, ruth)
    assert calls == ["Ruth 1-4"]


def test_fetch_passage_raises_without_api_key(monkeypatch, db_session, ruth):
    monkeypatch.setattr(esv_client, "ESV_API_KEY", "")
    with pytest.raises(esv_client.EsvApiError, match="ESV_API_KEY is not set"):
        esv_client.fetch_passage(db_session, ruth)


def test_fetch_passage_raises_on_non_200(monkeypatch, db_session, ruth):
    monkeypatch.setattr(esv_client, "ESV_API_KEY", "fake-key")
    monkeypatch.setattr(esv_client.httpx, "get", lambda *a, **k: httpx.Response(401, text="bad token"))
    with pytest.raises(esv_client.EsvApiError, match="401"):
        esv_client.fetch_passage(db_session, ruth)


def test_expired_cache_entry_is_refetched(monkeypatch, db_session, ruth):
    crud.upsert_passage_cache(
        db_session, ruth.id, "Ruth 1-4", "stale text", expires_at=utcnow() - timedelta(minutes=1)
    )
    monkeypatch.setattr(esv_client, "ESV_API_KEY", "fake-key")
    monkeypatch.setattr(esv_client.httpx, "get", lambda *a, **k: _fake_esv_response("fresh text"))

    text = esv_client.fetch_passage(db_session, ruth)
    assert text == "fresh text"
