# Scripture Quest

A gamified Bible-knowledge hub: pick a book, take a quiz generated fresh each time (grounded in the ESV), learn fun facts, and track streaks/XP/badges.

MVP scope: one book (Ruth) end-to-end before scaling to the rest. See `.claude/plans` in the parent session, or ask for the plan doc, for the full phased build order.

## Frontend

```
npm install
npm run dev      # http://localhost:5173
npm run test     # vitest
npm run lint     # oxlint
npm run build    # tsc -b && vite build
```

Reads `VITE_API_URL` (defaults to `http://localhost:8000`).

## Backend

```
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # fill in ESV_API_KEY + ANTHROPIC_API_KEY (see below), SESSION_SECRET
.venv/bin/uvicorn app.main:app --reload   # http://localhost:8000
.venv/bin/pytest
```

No `DATABASE_URL` needed for local dev — falls back to a SQLite file (`backend/dev.db`).

### API keys you'll need to get yourself

- **ESV API** — free key at https://api.esv.org/account/create-application/. Free tier: 5,000 queries/day, and no more than 500 verses (or half a book) cached at once — fine for Ruth, worth checking again before adding a long book.
- **Anthropic API** — key at https://console.anthropic.com/settings/keys. Used to generate quiz questions/fun facts about ESV text (never to recite it).

### Migrations

This project uses Alembic from the start (unlike sibling repos, which defer it) since it persists XP/streaks/badges from day one.

```
.venv/bin/alembic revision --autogenerate -m "message"
.venv/bin/alembic upgrade head
```
