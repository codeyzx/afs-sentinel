"""Single-password access (docs/system-rules.md §1): pages are public, writes need the admin password."""

from __future__ import annotations

import hmac
from urllib.parse import quote

from fastapi import Request
from fastapi.responses import RedirectResponse

SESSION_KEY = "is_admin"


def is_logged_in(request: Request) -> bool:
    return bool(request.session.get(SESSION_KEY))


def check_password(given: str, expected: str) -> bool:
    return bool(expected) and hmac.compare_digest(given.encode("utf-8"), expected.encode("utf-8"))


def login(request: Request) -> None:
    request.session[SESSION_KEY] = True


def logout(request: Request) -> None:
    request.session.pop(SESSION_KEY, None)


def safe_next(target: str | None) -> str:
    """Only allow local paths, to avoid open redirects."""
    if not target or not target.startswith("/") or target.startswith("//"):
        return "/"
    return target


def login_redirect(next_path: str) -> RedirectResponse:
    return RedirectResponse(f"/login?next={quote(safe_next(next_path), safe='/')}", status_code=303)


def flash(request: Request, message: str, tone: str = "gray") -> None:
    request.session.setdefault("flashes", [])
    request.session["flashes"] = [*request.session["flashes"], {"message": message, "tone": tone}]


def pop_flashes(request: Request) -> list[dict[str, str]]:
    return request.session.pop("flashes", []) if "flashes" in request.session else []
