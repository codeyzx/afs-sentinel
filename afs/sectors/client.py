"""Thin HTTP client for the Sectors API (docs/system-rules.md §2.1). Raw evidence in .scratch/api-verification/."""

from __future__ import annotations

import logging
import time
from datetime import date
from typing import Any, Callable

import httpx

from afs.config import get_settings

log = logging.getLogger(__name__)

RETRY_STATUSES = frozenset({500, 502, 503, 504})
RATE_LIMITED = 429
AUTH_STATUSES = frozenset({401, 403})
MAX_FILING_PAGES = 10


class SectorsApiError(RuntimeError):
    pass


class SectorsAuthError(SectorsApiError):
    """401/403: the key is invalid or its credits are exhausted. Nothing else will succeed either,
    so callers abort the whole run instead of failing every Emiten one by one."""


class SectorsClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        http: httpx.Client | None = None,
        retries: int = 2,
        backoff: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
        min_interval: float = 1.5,
        rate_limit_retries: int = 5,
        rate_limit_wait: float = 20.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        settings = get_settings()
        key = settings.sectors_api_key if api_key is None else api_key
        self._http = http or httpx.Client(timeout=30.0)
        self._base_url = (base_url or settings.sectors_base_url).rstrip("/")
        self._headers = {"Authorization": key}
        self._retries = retries
        self._backoff = backoff
        self._sleep = sleep
        # The API enforces a short burst limit (HTTP 429 RATE_LIMIT_EXCEEDED that clears within a minute),
        # so requests are spaced out and 429s wait much longer than ordinary transient errors.
        self._min_interval = min_interval
        self._rate_limit_retries = rate_limit_retries
        self._rate_limit_wait = rate_limit_wait
        self._clock = clock
        self._last_request: float | None = None
        self.credits_used = 0

    # ------------------------------------------------------------ transport

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self._base_url}{path}"
        attempt = 0
        limited = 0
        while True:
            self._throttle()
            try:
                resp = self._http.get(url, params=params, headers=self._headers, timeout=30.0)
            except httpx.TransportError as exc:
                if attempt < self._retries:
                    attempt += 1
                    self._sleep(self._backoff * 2 ** (attempt - 1))
                    continue
                raise SectorsApiError(f"GET {path} gagal: {exc}") from exc
            self._count_credits(resp)
            if resp.status_code == RATE_LIMITED and limited < self._rate_limit_retries:
                limited += 1
                wait = self._retry_after(resp) or min(self._rate_limit_wait * limited, 60.0)
                log.warning("Sectors API %s -> 429, tunggu %.0f dtk (percobaan %d)", path, wait, limited)
                self._sleep(wait)
                continue
            if resp.status_code in RETRY_STATUSES and attempt < self._retries:
                attempt += 1
                log.warning("Sectors API %s -> %s, retry %d", path, resp.status_code, attempt)
                self._sleep(self._backoff * 2 ** (attempt - 1))
                continue
            if resp.status_code in AUTH_STATUSES:
                raise SectorsAuthError(
                    f"GET {path} -> HTTP {resp.status_code}: API key tidak valid atau kredit habis"
                )
            if resp.status_code >= 400:
                raise SectorsApiError(f"GET {path} -> HTTP {resp.status_code}")
            try:
                return resp.json()
            except ValueError as exc:
                raise SectorsApiError(f"GET {path}: respons bukan JSON") from exc

    def _throttle(self) -> None:
        now = self._clock()
        if self._last_request is not None:
            wait = self._min_interval - (now - self._last_request)
            if wait > 0:
                self._sleep(wait)
                now = self._clock()
        self._last_request = now

    @staticmethod
    def _retry_after(resp: httpx.Response) -> float | None:
        try:
            return float(resp.headers["retry-after"])
        except (KeyError, ValueError):
            return None

    def _count_credits(self, resp: httpx.Response) -> None:
        raw = resp.headers.get("limit-consumption")
        if raw is None:
            return
        try:
            self.credits_used += int(float(raw))
        except ValueError:
            pass

    # ------------------------------------------------------------ endpoints

    def quarterly_dates(self, symbol: str) -> dict[str, list[list[str]]]:
        """{"2025": [["2025-03-31", "q1"], ...], ...}. No credit charge observed."""
        data = self._get(f"/v2/company/get_quarterly_financial_dates/{symbol}/")
        return data if isinstance(data, dict) else {}

    def quarterly(self, symbol: str, report_date: date) -> dict[str, Any] | None:
        """Exactly the requested quarter, or None. The API silently returns a later quarter when the
        requested one does not exist, so the returned date is checked."""
        data = self._get(f"/v2/financials/quarterly/{symbol}/", {"report_date": report_date.isoformat()})
        rows = data if isinstance(data, list) else []
        wanted = report_date.isoformat()
        for row in rows:
            if isinstance(row, dict) and str(row.get("date", ""))[:10] == wanted:
                return row
        return None

    def filings(self, symbol: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        params: dict[str, Any] = {"symbol": symbol}
        for _ in range(MAX_FILING_PAGES):
            data = self._get("/v2/filings/", params)
            if not isinstance(data, dict):
                break
            results.extend(r for r in data.get("results") or [] if isinstance(r, dict))
            pagination = data.get("pagination") or {}
            next_offset = pagination.get("next_offset")
            if not pagination.get("has_next") or next_offset is None:
                break
            params = {"symbol": symbol, "offset": next_offset}
        return results

    def corporate_actions(self, symbol: str) -> dict[str, Any]:
        data = self._get(f"/v2/company/corporate-actions/{symbol}/")
        return data if isinstance(data, dict) else {}

    def company_overview(self, symbol: str) -> dict[str, Any]:
        """{"symbol", "company_name", "overview": {"sector", "sub_sector", ...}}."""
        data = self._get(f"/v2/company/report/{symbol}/", {"sections": "overview"})
        return data if isinstance(data, dict) else {}
