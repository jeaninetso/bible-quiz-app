"""Seeds metadata for all 66 books of the Protestant canon (the ESV's canon —
no Apocrypha). Chapter counts cross-checked against two independent sources;
both testament subtotals (929 OT + 260 NT = 1,189) match the well-known
aggregate, so the per-book numbers below are verified, not guessed.

Only Ruth is `is_available=True` for the MVP — the rest show as "coming
soon" in the hub. Re-runnable: clears existing rows first so you can reseed
after model changes."""

from app import models
from app.database import Base, SessionLocal, engine

# (code, name, testament, chapter_count)
_OLD_TESTAMENT = [
    ("Gen", "Genesis", 50),
    ("Exod", "Exodus", 40),
    ("Lev", "Leviticus", 27),
    ("Num", "Numbers", 36),
    ("Deut", "Deuteronomy", 34),
    ("Josh", "Joshua", 24),
    ("Judg", "Judges", 21),
    ("Ruth", "Ruth", 4),
    ("1Sam", "1 Samuel", 31),
    ("2Sam", "2 Samuel", 24),
    ("1Kgs", "1 Kings", 22),
    ("2Kgs", "2 Kings", 25),
    ("1Chr", "1 Chronicles", 29),
    ("2Chr", "2 Chronicles", 36),
    ("Ezra", "Ezra", 10),
    ("Neh", "Nehemiah", 13),
    ("Esth", "Esther", 10),
    ("Job", "Job", 42),
    ("Ps", "Psalms", 150),
    ("Prov", "Proverbs", 31),
    ("Eccl", "Ecclesiastes", 12),
    ("Song", "Song of Solomon", 8),
    ("Isa", "Isaiah", 66),
    ("Jer", "Jeremiah", 52),
    ("Lam", "Lamentations", 5),
    ("Ezek", "Ezekiel", 48),
    ("Dan", "Daniel", 12),
    ("Hos", "Hosea", 14),
    ("Joel", "Joel", 3),
    ("Amos", "Amos", 9),
    ("Obad", "Obadiah", 1),
    ("Jonah", "Jonah", 4),
    ("Mic", "Micah", 7),
    ("Nah", "Nahum", 3),
    ("Hab", "Habakkuk", 3),
    ("Zeph", "Zephaniah", 3),
    ("Hag", "Haggai", 2),
    ("Zech", "Zechariah", 14),
    ("Mal", "Malachi", 4),
]

_NEW_TESTAMENT = [
    ("Matt", "Matthew", 28),
    ("Mark", "Mark", 16),
    ("Luke", "Luke", 24),
    ("John", "John", 21),
    ("Acts", "Acts", 28),
    ("Rom", "Romans", 16),
    ("1Cor", "1 Corinthians", 16),
    ("2Cor", "2 Corinthians", 13),
    ("Gal", "Galatians", 6),
    ("Eph", "Ephesians", 6),
    ("Phil", "Philippians", 4),
    ("Col", "Colossians", 4),
    ("1Thess", "1 Thessalonians", 5),
    ("2Thess", "2 Thessalonians", 3),
    ("1Tim", "1 Timothy", 6),
    ("2Tim", "2 Timothy", 4),
    ("Titus", "Titus", 3),
    ("Phlm", "Philemon", 1),
    ("Heb", "Hebrews", 13),
    ("Jas", "James", 5),
    ("1Pet", "1 Peter", 5),
    ("2Pet", "2 Peter", 3),
    ("1John", "1 John", 5),
    ("2John", "2 John", 1),
    ("3John", "3 John", 1),
    ("Jude", "Jude", 1),
    ("Rev", "Revelation", 22),
]

assert sum(c for _, _, c in _OLD_TESTAMENT) == 929
assert sum(c for _, _, c in _NEW_TESTAMENT) == 260
assert len(_OLD_TESTAMENT) == 39
assert len(_NEW_TESTAMENT) == 27

AVAILABLE_BOOK_CODE = "Ruth"


def build_books() -> list[models.Book]:
    books = []
    order_index = 0
    for testament, rows in (("old", _OLD_TESTAMENT), ("new", _NEW_TESTAMENT)):
        for code, name, chapter_count in rows:
            books.append(
                models.Book(
                    code=code,
                    name=name,
                    testament=testament,
                    chapter_count=chapter_count,
                    order_index=order_index,
                    is_available=(code == AVAILABLE_BOOK_CODE),
                )
            )
            order_index += 1
    return books


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.query(models.Book).delete()
        db.commit()
        db.add_all(build_books())
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    print(f"Seeded {len(_OLD_TESTAMENT) + len(_NEW_TESTAMENT)} books.")
