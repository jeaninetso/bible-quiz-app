"""Rate limiting for endpoints that are either expensive (quiz generation
spends Anthropic API credits per call) or brute-forceable (login).

Limits are env-configurable so they can be tuned per deployment without a
code change; defaults are picked for a small, mostly-trusted user base, not
a public-internet-scale product.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app import auth
from app.config import RATE_LIMIT_LOGIN, RATE_LIMIT_QUIZ


def _user_or_ip_key(request: Request) -> str:
    """Key by logged-in user id when available so a shared/proxied IP (e.g.
    everyone behind one Wi-Fi network) doesn't share a single quota; falls
    back to IP for unauthenticated requests (e.g. login attempts)."""
    cookie_value = request.cookies.get(auth.COOKIE_NAME)
    user_id = auth._read_user_id_from_cookie(cookie_value) if cookie_value else None
    return f"user:{user_id}" if user_id is not None else f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=_user_or_ip_key)
