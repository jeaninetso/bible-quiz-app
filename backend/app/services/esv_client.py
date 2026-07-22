"""Fetches real ESV verse text from Crossway's official ESV API. This is the
ONLY source of verse text in the app — the quiz-generation LLM (Phase 5) is
given this text to write questions about, never asked to recite Scripture
from its own training data (accuracy + copyright).

Caching is short-TTL (see PassageCache) per the ESV API's terms, which cap
cached/displayed text at 500 verses or half a book (whichever is less) and
encourage clearing cached text periodically. The API enforces this half-book
cap itself on any single contiguous range request — confirmed live, it isn't
just a caching guideline — so a `reference` passed in here must already name
a range that fits (see the quiz-section plan for how sections are chosen).
Never pass a bare book name: the ESV API silently resolves an unqualified
book name to chapter 1 only, which is NOT "the whole book" and previously
caused every Ruth quiz to be generated from chapter 1 alone."""

from datetime import timedelta

import httpx
from sqlalchemy.orm import Session

from app import crud, models
from app.config import ESV_API_KEY
from app.utils import utcnow

ESV_API_URL = "https://api.esv.org/v3/passage/text/"
CACHE_TTL = timedelta(hours=1)


class EsvApiError(Exception):
    pass


def _fetch_from_esv_api(reference: str) -> str:
    if not ESV_API_KEY:
        raise EsvApiError("ESV_API_KEY is not set — copy backend/.env.example to .env and fill it in.")

    try:
        response = httpx.get(
            ESV_API_URL,
            params={
                "q": reference,
                "include-headings": "false",
                "include-footnotes": "false",
                "include-verse-numbers": "true",
                "include-short-copyright": "true",
            },
            headers={"Authorization": f"Token {ESV_API_KEY}"},
            timeout=10.0,
        )
    except httpx.RequestError as exc:
        raise EsvApiError(f"Could not reach the ESV API: {exc}") from exc

    if response.status_code != 200:
        raise EsvApiError(f"ESV API returned {response.status_code}: {response.text}")

    data = response.json()
    passages = data.get("passages", [])
    if not passages:
        raise EsvApiError(f"ESV API returned no text for '{reference}' — check the reference is valid.")
    return "\n\n".join(passages).strip()


def fetch_passage(db: Session, book: models.Book, reference: str | None = None) -> str:
    """Returns ESV text for `reference` (defaults to the whole book, as an
    explicit chapter range — never just `book.name`, since the ESV API
    silently treats a bare book name as "chapter 1 only"), using the
    short-TTL cache when available."""
    reference = reference or f"{book.name} 1-{book.chapter_count}"

    cached = crud.get_cached_passage(db, book.id, reference)
    if cached is not None:
        return cached.esv_text

    text = _fetch_from_esv_api(reference)
    crud.upsert_passage_cache(db, book.id, reference, text, expires_at=utcnow() + CACHE_TTL)
    return text
