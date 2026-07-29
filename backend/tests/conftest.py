import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.rate_limit import limiter


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    # The limiter's in-memory storage lives on the module-level `app`
    # singleton, so hit counts would otherwise accumulate across every test
    # in the run (all sharing the same client key) and spuriously trip
    # limits meant for real abusive traffic, not test volume.
    limiter.reset()
    yield


@pytest.fixture()
def db_session():
    # In-memory SQLite stands in for Postgres in tests — StaticPool keeps a
    # single connection alive so the schema/data persist across queries
    # within a test (a fresh in-memory DB per connection would otherwise
    # look empty on the second query).
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
