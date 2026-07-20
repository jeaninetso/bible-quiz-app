from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Scripture Quest API")

# Local dev only — Vite may pick a different port if 5173 is taken.
# Tighten this to a specific origin (and enable allow_credentials) once
# Phase 2 adds session-cookie auth.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}
