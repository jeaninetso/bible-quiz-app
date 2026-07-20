from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC now — SQLite round-trips stored datetimes as naive, so this
    stays comparable to values read back from the DB (datetime.utcnow() is
    deprecated; this is its non-deprecated equivalent)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
