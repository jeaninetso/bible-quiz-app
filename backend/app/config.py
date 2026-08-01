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

SESSION_SECRET = os.environ.get("SESSION_SECRET", "dev-only-insecure-secret")

# Browsers reject Secure cookies over plain http — keep this false for local
# dev, set COOKIE_SECURE=true once this is ever served over https.
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "http://localhost:5173")

ESV_API_KEY = os.environ.get("ESV_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# One-line swap if quiz quality needs a stronger model later.
QUIZ_MODEL = os.environ.get("QUIZ_MODEL", "claude-haiku-4-5")
