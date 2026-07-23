"""Seeds quiz Sections — the actual quiz-generation targets. See Section's
docstring in app/models.py for why a Book alone can never be one: the ESV
API hard-caps any single contiguous chapter-range request at half a book's
verses (or 500, whichever is less), confirmed against the live API.

Every reference/verse-count pair below was verified directly against the
ESV API before seeding (see the section plan) — not estimated from a
verse-count table. Only Ruth and Genesis have sections so far; the other
~64 books get none yet and stay "coming soon" with nothing to enumerate.
Extending to another book is adding a row here (after verifying the split
against the live API), not more architecture.

Re-runnable: clears existing rows first. Resolves `book_id` by looking up
Book.code, never a hardcoded id — seed_books.py's reseed is destructive, so
Book ids are not stable across runs."""

from app import models
from app.database import Base, SessionLocal, engine

# book_code -> [(display name, ESV reference, verse count as last verified)]
_SECTIONS = {
    "Ruth": [
        ("Ruth 1–2", "Ruth 1-2", 42),
        ("Ruth 3–4", "Ruth 3-4", 40),
    ],
    "Gen": [
        ("Primeval History", "Genesis 1-11", 299),
        ("Abraham", "Genesis 12-25", 394),
        ("Isaac & Jacob", "Genesis 26-36", 391),
        ("Joseph", "Genesis 37-50", 449),
    ],
}


def build_sections(db) -> list[models.Section]:
    books_by_code = {b.code: b for b in db.query(models.Book).all()}
    sections = []
    for book_code, rows in _SECTIONS.items():
        book = books_by_code[book_code]
        for order_index, (name, reference, _verse_count) in enumerate(rows):
            sections.append(
                models.Section(
                    book_id=book.id,
                    name=name,
                    reference=reference,
                    order_index=order_index,
                    is_available=True,
                )
            )
    return sections


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(models.Section).delete()
        db.commit()
        db.add_all(build_sections(db))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    total = sum(len(rows) for rows in _SECTIONS.values())
    print(f"Seeded {total} sections across {len(_SECTIONS)} books.")
