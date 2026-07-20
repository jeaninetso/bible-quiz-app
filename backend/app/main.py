from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGIN
from app.routers import auth as auth_router
from app.routers import books as books_router

app = FastAPI(title="Scripture Quest API")

# Credentialed requests (cookies) require an exact origin, not a wildcard or
# regex — browsers reject Access-Control-Allow-Origin: * when credentials
# are involved. CORS_ORIGIN defaults to the Vite dev port; override it once
# this is ever deployed somewhere else.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(books_router.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
