"""Thin HTTP client for the Sectors API (docs/system-rules.md §2.1). Raw evidence in .scratch/api-verification/."""

from __future__ import annotations

import logging
import time
from datetime import date
from typing import Any, Callable

import httpx

from afs.config import get_settings

log = logging.getLogger(__name__)

RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
MAX_FILING_PAGES = 10


class SectorsApiError(RuntimeError):
    pass


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
    ) -> None:
        settings = get_settings()
        key = settings.sectors_api_key if api_key is None else api_key
        self._http = http or httpx.Client(timeout=30.0)
        self._base_url = (base_url or settings.sectors_base_url).rstrip("/")
        self._headers = {"Authorization": key}
        self._retries = retries
        self._backoff = backoff
        self._sleep = sleep
        self.credits_used = 0

    # ------------------------------------------------------------ transport

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self._base_url}{path}"
        attempt = 0
        while True:
            try:
                resp = self._http.get(url, params=params, headers=self._headers, timeout=30.0)
            except httpx.TransportError as exc:
                if attempt < self._retries:
                    attempt += 1
                    self._sleep(self._backoff * 2 ** (attempt - 1))
                    continue
                raise SectorsApiError(f"GET {path} gagal: {exc}") from exc
            self._count_credits(resp)
            if resp.status_code in RETRY_STATUSES and attempt < self._retries:
                attempt += 1
                log.warning("Sectors API %s -> %s, retry %d", path, resp.status_code, attempt)
                self._sleep(self._backoff * 2 ** (attempt - 1))
                continue
            if resp.status_code >= 400:
                raise SectorsApiError(f"GET {path} -> HTTP {resp.status_code}")
            try:
                return resp.json()
            except ValueError as exc:
                raise SectorsApiError(f"GET {path}: respons bukan JSON") from exc

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
