"""Seeds quiz Sections — the actual quiz-generation targets. See Section's
docstring in app/models.py for why a Book alone can never be one: the ESV
API hard-caps any single contiguous chapter-range request (confirmed live
— no formula predicts the cap reliably; every range below was verified
against the live API, not estimated).

Every book now has verified sections. Where a real, recognized scholarly
or traditional division exists (Genesis's patriarchal narratives, the
Torah's Exodus/Numbers turning points, Psalms' 5 traditional "Books",
Proverbs' collections, Isaiah's judgment/comfort split), sections follow
it — split further only where a piece still exceeds the API's cap. Every
other book falls back to plain, roughly-even chapter chunking, verified
live rather than assumed.

Only Ruth and Genesis are unlocked (is_available=True) — everything else
seeds locked (is_available=False) per the incremental-rollout plan: flip a
book on in _AVAILABLE_BOOK_CODES below only after spot-checking its quiz
quality.

Re-runnable: clears existing rows first. Resolves `book_id` by looking up
Book.code, never a hardcoded id — seed_books.py's reseed is destructive, so
Book ids are not stable across runs."""

from app import models
from app.database import Base, SessionLocal, engine

_AVAILABLE_BOOK_CODES = {"Ruth", "Gen"}

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
    "Exod": [
        ("Israel in Egypt & the Exodus", "Exodus 1:1-18:999", 494),
        ("Sinai: Covenant & Law (part 1)", "Exodus 19:1-30:999", 394),
        ("Sinai: Covenant & Law (part 2)", "Exodus 31:1-40:999", 325),
    ],
    "Lev": [
        ("Ch 1-9", "Leviticus 1:1-9:999", 232),
        ("Ch 10-15", "Leviticus 10:1-15:999", 224),
        ("Ch 16-27", "Leviticus 16:1-27:999", 403),
    ],
    "Num": [
        ("The Old Generation (Wilderness) (part 1)", "Numbers 1:1-11:999", 455),
        ("The Old Generation (Wilderness) (part 2)", "Numbers 12:1-25:999", 430),
        ("The New Generation (Plains of Moab)", "Numbers 26:1-36:999", 403),
    ],
    "Deut": [
        ("Ch 1-8", "Deuteronomy 1:1-8:999", 265),
        ("Ch 9-17", "Deuteronomy 9:1-17:999", 227),
        ("Ch 18-34", "Deuteronomy 18:1-34:999", 467),
    ],
    "Josh": [
        ("Ch 1-8", "Joshua 1:1-8:999", 186),
        ("Ch 9-13", "Joshua 9:1-13:999", 150),
        ("Ch 14-24", "Joshua 14:1-24:999", 322),
    ],
    "Judg": [
        ("Ch 1-6", "Judges 1:1-6:999", 185),
        ("Ch 7-10", "Judges 7:1-10:999", 135),
        ("Ch 11-21", "Judges 11:1-21:999", 298),
    ],
    "1Sam": [
        ("Ch 1-9", "1 Samuel 1:1-9:999", 206),
        ("Ch 10-16", "1 Samuel 10:1-16:999", 200),
        ("Ch 17-31", "1 Samuel 17:1-31:999", 404),
    ],
    "2Sam": [
        ("Ch 1-7", "2 Samuel 1:1-7:999", 187),
        ("Ch 8-14", "2 Samuel 8:1-14:999", 180),
        ("Ch 15-24", "2 Samuel 15:1-24:999", 328),
    ],
    "1Kgs": [
        ("Ch 1-6", "1 Kings 1:1-6:999", 217),
        ("Ch 7-11", "1 Kings 7:1-11:999", 217),
        ("Ch 12-22", "1 Kings 12:1-22:999", 382),
    ],
    "2Kgs": [
        ("Ch 1-7", "2 Kings 1:1-7:999", 194),
        ("Ch 8-13", "2 Kings 8:1-13:999", 169),
        ("Ch 14-25", "2 Kings 14:1-25:999", 356),
    ],
    "1Chr": [
        ("Ch 1-6", "1 Chronicles 1:1-6:999", 283),
        ("Ch 7-12", "1 Chronicles 7:1-12:999", 225),
        ("Ch 13-29", "1 Chronicles 13:1-29:999", 434),
    ],
    "2Chr": [
        ("Ch 1-10", "2 Chronicles 1:1-10:999", 220),
        ("Ch 11-20", "2 Chronicles 11:1-20:999", 210),
        ("Ch 21-36", "2 Chronicles 21:1-36:999", 392),
    ],
    "Ezra": [
        ("Ch 1-2", "Ezra 1:1-2:999", 81),
        ("Ch 3-6", "Ezra 3:1-6:999", 76),
        ("Ch 7-10", "Ezra 7:1-10:999", 123),
    ],
    "Neh": [
        ("Ch 1-6", "Nehemiah 1:1-6:999", 124),
        ("Ch 7-8", "Nehemiah 7:1-8:999", 91),
        ("Ch 9-13", "Nehemiah 9:1-13:999", 191),
    ],
    "Esth": [
        ("Ch 1-3", "Esther 1:1-3:999", 60),
        ("Ch 4-5", "Esther 4:1-5:999", 31),
        ("Ch 6-10", "Esther 6:1-10:999", 76),
    ],
    "Job": [
        ("Ch 1-12", "Job 1:1-12:999", 284),
        ("Ch 13-22", "Job 13:1-22:999", 266),
        ("Ch 23-33", "Job 23:1-33:999", 264),
        ("Ch 34-42", "Job 34:1-42:999", 256),
    ],
    "Ps": [
        ("Book I (part 1)", "Psalms 1:1-24:999", 312),
        ("Book I (part 2)", "Psalms 25:1-41:999", 304),
        ("Book II", "Psalms 42:1-72:999", 465),
        ("Book III", "Psalms 73:1-89:999", 358),
        ("Book IV", "Psalms 90:1-106:999", 321),
        ("Book V (part 1)", "Psalms 107:1-119:999", 375),
        ("Book V (part 2)", "Psalms 120:1-150:999", 326),
    ],
    "Prov": [
        ("Wisdom's Appeal", "Proverbs 1:1-9:999", 256),
        ("Proverbs of Solomon", "Proverbs 10:1-24:999", 457),
        ("Hezekiah's Collection & Sayings of Agur and Lemuel", "Proverbs 25:1-31:999", 202),
    ],
    "Eccl": [
        ("Ch 1-3", "Ecclesiastes 1:1-3:999", 66),
        ("Ch 4-6", "Ecclesiastes 4:1-6:999", 48),
        ("Ch 7-12", "Ecclesiastes 7:1-12:999", 108),
    ],
    "Song": [
        ("Ch 1-2", "Song of Solomon 1:1-2:999", 34),
        ("Ch 3-4", "Song of Solomon 3:1-4:999", 27),
        ("Ch 5-8", "Song of Solomon 5:1-8:999", 56),
    ],
    "Isa": [
        ("Judgment (Isaiah 1-39) (part 1)", "Isaiah 1:1-21:999", 398),
        ("Judgment (Isaiah 1-39) (part 2)", "Isaiah 22:1-39:999", 368),
        ("Comfort (Isaiah 40-66) (part 1)", "Isaiah 40:1-51:999", 276),
        ("Comfort (Isaiah 40-66) (part 2)", "Isaiah 52:1-66:999", 250),
    ],
    "Jer": [
        ("Ch 1-13", "Jeremiah 1:1-13:999", 347),
        ("Ch 14-28", "Jeremiah 14:1-28:999", 342),
        ("Ch 29-41", "Jeremiah 29:1-41:999", 340),
        ("Ch 42-52", "Jeremiah 42:1-52:999", 335),
    ],
    "Lam": [
        ("Ch 1-2", "Lamentations 1:1-2:999", 44),
        ("Ch 3", "Lamentations 3:1-3:999", 66),
        ("Ch 4-5", "Lamentations 4:1-5:999", 44),
    ],
    "Ezek": [
        ("Ch 1-16", "Ezekiel 1:1-16:999", 361),
        ("Ch 17-26", "Ezekiel 17:1-26:999", 296),
        ("Ch 27-38", "Ezekiel 27:1-38:999", 327),
        ("Ch 39-48", "Ezekiel 39:1-48:999", 289),
    ],
    "Dan": [
        ("Ch 1-3", "Daniel 1:1-3:999", 100),
        ("Ch 4-6", "Daniel 4:1-6:999", 96),
        ("Ch 7-12", "Daniel 7:1-12:999", 161),
    ],
    "Hos": [
        ("Ch 1-4", "Hosea 1:1-4:999", 58),
        ("Ch 5-7", "Hosea 5:1-7:999", 42),
        ("Ch 8-14", "Hosea 8:1-14:999", 97),
    ],
    "Joel": [
        ("Ch 1", "Joel 1:1-1:999", 20),
        ("Ch 2", "Joel 2:1-2:999", 32),
        ("Ch 3", "Joel 3:1-3:999", 21),
    ],
    "Amos": [
        ("Ch 1-3", "Amos 1:1-3:999", 46),
        ("Ch 4-5", "Amos 4:1-5:999", 40),
        ("Ch 6-9", "Amos 6:1-9:999", 60),
    ],
    "Obad": [
        ("Obadiah", "Obadiah 1:1-1:999", 21),
    ],
    "Jonah": [
        ("Ch 1", "Jonah 1:1-1:999", 17),
        ("Ch 2", "Jonah 2:1-2:999", 10),
        ("Ch 3-4", "Jonah 3:1-4:999", 21),
    ],
    "Mic": [
        ("Ch 1-2", "Micah 1:1-2:999", 29),
        ("Ch 3-4", "Micah 3:1-4:999", 25),
        ("Ch 5-7", "Micah 5:1-7:999", 51),
    ],
    "Nah": [
        ("Ch 1", "Nahum 1:1-1:999", 15),
        ("Ch 2", "Nahum 2:1-2:999", 13),
        ("Ch 3", "Nahum 3:1-3:999", 19),
    ],
    "Hab": [
        ("Ch 1", "Habakkuk 1:1-1:999", 17),
        ("Ch 2", "Habakkuk 2:1-2:999", 20),
        ("Ch 3", "Habakkuk 3:1-3:999", 19),
    ],
    "Zeph": [
        ("Ch 1", "Zephaniah 1:1-1:999", 18),
        ("Ch 2", "Zephaniah 2:1-2:999", 15),
        ("Ch 3", "Zephaniah 3:1-3:999", 20),
    ],
    "Hag": [
        ("Haggai", "Haggai 1:1-2:999", 38),
    ],
    "Zech": [
        ("Ch 1-5", "Zechariah 1:1-5:999", 69),
        ("Ch 6-8", "Zechariah 6:1-8:999", 52),
        ("Ch 9-14", "Zechariah 9:1-14:999", 90),
    ],
    "Mal": [
        ("Ch 1", "Malachi 1:1-1:999", 14),
        ("Ch 2", "Malachi 2:1-2:999", 17),
        ("Ch 3-4", "Malachi 3:1-4:999", 24),
    ],
    "Matt": [
        ("Ch 1-10", "Matthew 1:1-10:999", 315),
        ("Ch 11-16", "Matthew 11:1-16:999", 241),
        ("Ch 17-24", "Matthew 17:1-24:999", 308),
        ("Ch 25-28", "Matthew 25:1-28:999", 207),
    ],
    "Mark": [
        ("Ch 1-5", "Mark 1:1-5:999", 192),
        ("Ch 6-9", "Mark 6:1-9:999", 181),
        ("Ch 10-16", "Mark 10:1-16:999", 305),
    ],
    "Luke": [
        ("Ch 1-7", "Luke 1:1-7:999", 352),
        ("Ch 8-12", "Luke 8:1-12:999", 273),
        ("Ch 13-20", "Luke 13:1-20:999", 308),
        ("Ch 21-24", "Luke 21:1-24:999", 218),
    ],
    "John": [
        ("Ch 1-6", "John 1:1-6:999", 284),
        ("Ch 7-10", "John 7:1-10:999", 195),
        ("Ch 11-21", "John 11:1-21:999", 400),
    ],
    "Acts": [
        ("Ch 1-8", "Acts 1:1-8:999", 293),
        ("Ch 9-14", "Acts 9:1-14:999", 226),
        ("Ch 15-28", "Acts 15:1-28:999", 488),
    ],
    "Rom": [
        ("Ch 1-4", "Romans 1:1-4:999", 117),
        ("Ch 5-8", "Romans 5:1-8:999", 108),
        ("Ch 9-16", "Romans 9:1-16:999", 208),
    ],
    "1Cor": [
        ("Ch 1-6", "1 Corinthians 1:1-6:999", 124),
        ("Ch 7-10", "1 Corinthians 7:1-10:999", 113),
        ("Ch 11-16", "1 Corinthians 11:1-16:999", 200),
    ],
    "2Cor": [
        ("Ch 1-4", "2 Corinthians 1:1-4:999", 77),
        ("Ch 5-7", "2 Corinthians 5:1-7:999", 55),
        ("Ch 8-13", "2 Corinthians 8:1-13:999", 125),
    ],
    "Gal": [
        ("Ch 1-3", "Galatians 1:1-3:999", 74),
        ("Ch 4", "Galatians 4:1-4:999", 31),
        ("Ch 5-6", "Galatians 5:1-6:999", 44),
    ],
    "Eph": [
        ("Ch 1-3", "Ephesians 1:1-3:999", 66),
        ("Ch 4", "Ephesians 4:1-4:999", 32),
        ("Ch 5-6", "Ephesians 5:1-6:999", 57),
    ],
    "Phil": [
        ("Ch 1", "Philippians 1:1-1:999", 30),
        ("Ch 2", "Philippians 2:1-2:999", 30),
        ("Ch 3-4", "Philippians 3:1-4:999", 44),
    ],
    "Col": [
        ("Ch 1", "Colossians 1:1-1:999", 29),
        ("Ch 2", "Colossians 2:1-2:999", 23),
        ("Ch 3-4", "Colossians 3:1-4:999", 43),
    ],
    "1Thess": [
        ("Ch 1-3", "1 Thessalonians 1:1-3:999", 43),
        ("Ch 4", "1 Thessalonians 4:1-4:999", 18),
        ("Ch 5", "1 Thessalonians 5:1-5:999", 28),
    ],
    "2Thess": [
        ("Ch 1", "2 Thessalonians 1:1-1:999", 12),
        ("Ch 2", "2 Thessalonians 2:1-2:999", 17),
        ("Ch 3", "2 Thessalonians 3:1-3:999", 18),
    ],
    "1Tim": [
        ("Ch 1-2", "1 Timothy 1:1-2:999", 35),
        ("Ch 3-4", "1 Timothy 3:1-4:999", 32),
        ("Ch 5-6", "1 Timothy 5:1-6:999", 46),
    ],
    "2Tim": [
        ("Ch 1", "2 Timothy 1:1-1:999", 18),
        ("Ch 2", "2 Timothy 2:1-2:999", 26),
        ("Ch 3-4", "2 Timothy 3:1-4:999", 39),
    ],
    "Titus": [
        ("Ch 1", "Titus 1:1-1:999", 16),
        ("Ch 2", "Titus 2:1-2:999", 15),
        ("Ch 3", "Titus 3:1-3:999", 15),
    ],
    "Phlm": [
        ("Philemon", "Philemon 1:1-1:999", 25),
    ],
    "Heb": [
        ("Ch 1-6", "Hebrews 1:1-6:999", 101),
        ("Ch 7-9", "Hebrews 7:1-9:999", 69),
        ("Ch 10-13", "Hebrews 10:1-13:999", 133),
    ],
    "Jas": [
        ("Ch 1-2", "James 1:1-2:999", 53),
        ("Ch 3", "James 3:1-3:999", 18),
        ("Ch 4-5", "James 4:1-5:999", 37),
    ],
    "1Pet": [
        ("Ch 1-2", "1 Peter 1:1-2:999", 50),
        ("Ch 3", "1 Peter 3:1-3:999", 22),
        ("Ch 4-5", "1 Peter 4:1-5:999", 33),
    ],
    "2Pet": [
        ("Ch 1", "2 Peter 1:1-1:999", 21),
        ("Ch 2", "2 Peter 2:1-2:999", 22),
        ("Ch 3", "2 Peter 3:1-3:999", 18),
    ],
    "1John": [
        ("Ch 1-2", "1 John 1:1-2:999", 39),
        ("Ch 3", "1 John 3:1-3:999", 24),
        ("Ch 4-5", "1 John 4:1-5:999", 42),
    ],
    "2John": [
        ("2 John", "2 John 1:1-1:999", 13),
    ],
    "3John": [
        ("3 John", "3 John 1:1-1:999", 15),
    ],
    "Jude": [
        ("Jude", "Jude 1:1-1:999", 25),
    ],
    "Rev": [
        ("Ch 1-6", "Revelation 1:1-6:999", 113),
        ("Ch 7-12", "Revelation 7:1-12:999", 98),
        ("Ch 13-22", "Revelation 13:1-22:999", 193),
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
                    is_available=book_code in _AVAILABLE_BOOK_CODES,
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
