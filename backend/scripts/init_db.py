"""Create all tables directly — used only as a quick local escape hatch.
Real schema changes go through Alembic (see backend/migrations/)."""

from app import models  # noqa: F401 — import registers models on Base.metadata
from app.database import Base, engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Tables created.")
