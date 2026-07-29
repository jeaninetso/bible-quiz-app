import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent

# Anchored to an absolute path — load_dotenv() with no argument searches
# upward from the process's cwd, which silently misses backend/.env when
# uvicorn is launched from elsewhere.
load_dotenv(BACKEND_DIR / ".env")

# SQLite fallback lets the app boot with zero setup. Real dev/prod always
# points DATABASE_URL at Postgres instead.
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'dev.db'}")

# Hosts that provision Postgres for you (Render, Heroku-style providers) hand
# back a bare "postgres://" or "postgresql://" URL, which makes SQLAlchemy
# default to the psycopg2 driver — not installed here, we use psycopg (v3)
# instead (see requirements.txt). Force the +psycopg driver onto whatever
# scheme we're given so this works regardless of where the URL came from.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgres://") :]
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgresql://") :]

SESSION_SECRET = os.environ.get("SESSION_SECRET", "dev-only-insecure-secret")

# Browsers reject Secure cookies over plain http — keep this false for local
# dev, set COOKIE_SECURE=true once this is ever served over https.
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "http://localhost:5173")

ESV_API_KEY = os.environ.get("ESV_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# One-line swap if quiz quality needs a stronger model later.
QUIZ_MODEL = os.environ.get("QUIZ_MODEL", "claude-haiku-4-5")

# slowapi rate-limit strings ("N/second|minute|hour|day"). Quiz generation
# costs real Anthropic credits per call; login is the brute-forceable
# endpoint. Defaults assume a small, mostly-trusted user base — tighten for
# a public deployment.
RATE_LIMIT_LOGIN = os.environ.get("RATE_LIMIT_LOGIN", "10/minute")
RATE_LIMIT_QUIZ = os.environ.get("RATE_LIMIT_QUIZ", "20/hour")
