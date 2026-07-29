from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import CORS_ORIGIN
from app.rate_limit import limiter
from app.routers import auth as auth_router
from app.routers import books as books_router
from app.routers import quiz as quiz_router
from app.routers import quiz_attempts as quiz_attempts_router
from app.routers import stats as stats_router

app = FastAPI(title="Scripture Quest API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

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
app.include_router(quiz_router.router)
app.include_router(quiz_attempts_router.router)
app.include_router(stats_router.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
