"""Data access for the Forensic Rules: Sectors API behind a permanent Postgres cache (docs/system-rules.md §2.2).

Cache layout (models.ApiCache):
- kind="quarter", key=report_date ISO: raw API row, or {"missing": true}. Never re-fetched.
- kind="quarter_dates" | "filings" | "corporate_actions", key=fetch date ISO: at most one fetch per day.
- kind="corporate_actions", key="backtest": fetched once for Backtests.
- kind="company", key="": company overview, fetched once.

The repository only flushes; the caller owns the transaction (commit it even when later work fails,
otherwise paid-for quarters are lost).
"""

from __future__ import annotations

import calendar
import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from afs.config import WIB, get_settings
from afs.domain import Dividend, EvaluationInput, Filing, Quarter
from afs.models import ApiCache, Emiten
from afs.sectors.client import SectorsClient

log = logging.getLogger(__name__)

WINDOW = 5  # t, t-1 .. t-4
FINANCIAL_MARKERS = ("financ", "bank", "insurance", "asuransi")


def _today_wib() -> date:
    return datetime.now(WIB).date()


# ---------------------------------------------------------------- pure helpers


def quarter_end_before(report_date: date, k: int) -> date:
    """Calendar quarter-end k quarters before report_date (report_date is itself a quarter-end)."""
    index = report_date.year * 12 + (report_date.month - 1) - 3 * k
    year, month = divmod(index, 12)
    month += 1
    return date(year, month, calendar.monthrange(year, month)[1])


def parse_report_dates(payload: Any) -> list[date]:
    """{"2025": [["2025-03-31", "q1"], ...]} -> sorted unique dates."""
    out: set[date] = set()
    if isinstance(payload, dict):
        for rows in payload.values():
            for row in rows or []:
                raw = row[0] if isinstance(row, (list, tuple)) and row else row
                parsed = _parse_date(raw)
                if parsed:
                    out.add(parsed)
    return sorted(out)


def _parse_date(raw: Any) -> date | None:
    if not isinstance(raw, str) or len(raw) < 10:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _parse_timestamp(raw: Any) -> datetime | None:
    if not isinstance(raw, str) or not raw:
        return None
    try:
        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return ts.replace(tzinfo=WIB) if ts.tzinfo is None else ts  # naive API timestamps are WIB


def _float(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def parse_filings(rows: Any) -> list[Filing]:
    out: list[Filing] = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        ts = _parse_timestamp(row.get("timestamp"))
        if ts is None:
            continue
        out.append(
            Filing(
                timestamp=ts,
                transaction_type=str(row.get("transaction_type") or "others"),
                holder_type=str(row.get("holder_type") or ""),
                holder_name=str(row.get("holder_name") or ""),
                share_percentage_transaction=_float(row.get("share_percentage_transaction")),
                amount_transaction=_float(row.get("amount_transaction")),
                price=_float(row.get("price")),
            )
        )
    return out


def parse_dividends(payload: Any) -> list[Dividend]:
    """Dividends from a corporate-actions body, sorted by ex_date. Null sections mean none."""
    actions = payload.get("corporate_actions") if isinstance(payload, dict) else None
    rows = actions.get("dividend") if isinstance(actions, dict) else None
    out: list[Dividend] = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        ex = _parse_date(row.get("ex_date"))
        if ex is None:
            continue
        out.append(Dividend(ex_date=ex, amount=_float(row.get("dividend_amount"))))
    return sorted(out, key=lambda d: d.ex_date)


def is_financial_sector(*labels: str) -> bool:
    text = " ".join(labels).lower()
    return any(marker in text for marker in FINANCIAL_MARKERS)


# ---------------------------------------------------------------- repository


class DataRepository:
    def __init__(
        self, session: Session, client: SectorsClient, *, today: Callable[[], date] = _today_wib
    ) -> None:
        self.session = session
        self.client = client
        self._today = today

    # ------------------------------------------------------------ cache primitives

    def _cached(self, kind: str, symbol: str, key: str) -> ApiCache | None:
        return self.session.scalar(
            select(ApiCache).where(ApiCache.kind == kind, ApiCache.symbol == symbol, ApiCache.key == key)
        )

    def _store(self, kind: str, symbol: str, key: str, payload: Any) -> None:
        self.session.add(ApiCache(kind=kind, symbol=symbol, key=key, payload=payload))
        self.session.flush()

    def _cached_or_fetch(self, kind: str, symbol: str, key: str, fetch: Callable[[], Any]) -> Any:
        hit = self._cached(kind, symbol, key)
        if hit is not None:
            return hit.payload
        payload = fetch()
        self._store(kind, symbol, key, payload)
        return payload

    # ------------------------------------------------------------ quarters

    def _report_dates(self, symbol: str, as_of: date) -> list[date]:
        payload = self._cached_or_fetch(
            "quarter_dates", symbol, as_of.isoformat(), lambda: self.client.quarterly_dates(symbol)
        )
        return parse_report_dates(payload)

    def available_report_dates(self, symbol: str) -> list[date]:
        return self._report_dates(symbol, self._today())

    def _quarter(self, symbol: str, report_date: date, known: set[date]) -> Quarter | None:
        hit = self._cached("quarter", symbol, report_date.isoformat())
        if hit is not None:
            payload = hit.payload
        elif report_date not in known:
            return None  # the API lists no such Report Period: don't spend a credit
        else:
            row = self.client.quarterly(symbol, report_date)
            payload = row if row is not None else {"missing": True}
            self._store("quarter", symbol, report_date.isoformat(), payload)
        if not isinstance(payload, dict) or payload.get("missing"):
            return None
        return Quarter(report_date=report_date, data=payload)

    def _window(self, symbol: str, t: date, known: set[date]) -> list[Quarter | None]:
        return [self._quarter(symbol, quarter_end_before(t, k), known) for k in range(WINDOW)]

    # ------------------------------------------------------------ public API

    def build_live_input(self, symbol: str, as_of: date) -> EvaluationInput | None:
        dates = [d for d in self._report_dates(symbol, as_of) if d <= as_of]
        if not dates:
            return None
        quarters = self._window(symbol, dates[-1], set(dates))
        if quarters[0] is None:
            return None

        filings: list[Filing] | None
        try:
            filings = parse_filings(
                self._cached_or_fetch("filings", symbol, as_of.isoformat(), lambda: self.client.filings(symbol))
            )
        except Exception as exc:  # noqa: BLE001 - any failure -> INSUFFICIENT_DATA downstream
            log.warning("filings %s gagal: %s", symbol, exc)
            filings = None

        dividends: list[Dividend] | None
        try:
            dividends = parse_dividends(
                self._cached_or_fetch(
                    "corporate_actions", symbol, as_of.isoformat(), lambda: self.client.corporate_actions(symbol)
                )
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("corporate actions %s gagal: %s", symbol, exc)
            dividends = None

        return EvaluationInput(symbol=symbol, quarters=quarters, as_of=as_of, filings=filings, dividends=dividends)

    def build_backtest_input(self, symbol: str, report_date: date) -> EvaluationInput:
        known = set(self.available_report_dates(symbol)) | {report_date}
        quarters = self._window(symbol, report_date, known)
        dividends: list[Dividend] | None
        try:
            payload = self._cached_or_fetch(
                "corporate_actions", symbol, "backtest", lambda: self.client.corporate_actions(symbol)
            )
            dividends = [d for d in parse_dividends(payload) if d.ex_date <= report_date]
        except Exception as exc:  # noqa: BLE001
            log.warning("corporate actions %s gagal: %s", symbol, exc)
            dividends = None
        return EvaluationInput(
            symbol=symbol,
            quarters=quarters,
            as_of=report_date,
            filings=None,
            dividends=dividends,
            is_backtest=True,
        )

    def quarters_for_chart(
        self, symbol: str, report_date: date, n: int = 5
    ) -> list[tuple[date, float | None, float | None]]:
        """(report_date, earnings, operating_cash_flow), oldest first, from cache only."""
        out: list[tuple[date, float | None, float | None]] = []
        for k in reversed(range(n)):
            d = quarter_end_before(report_date, k)
            hit = self._cached("quarter", symbol, d.isoformat())
            payload = hit.payload if hit is not None and isinstance(hit.payload, dict) else {}
            if payload.get("missing"):
                payload = {}
            out.append((d, _float(payload.get("earnings")), _float(payload.get("operating_cash_flow"))))
        return out

    def company_overview(self, symbol: str) -> dict[str, Any]:
        payload = self._cached_or_fetch("company", symbol, "", lambda: self.client.company_overview(symbol))
        return payload if isinstance(payload, dict) else {}

    def sync_universe(self, path: Path | None = None) -> list[Emiten]:
        config = json.loads((path or get_settings().universe_path).read_text())
        symbols = list(dict.fromkeys(str(s).strip().upper() for s in config.get("symbols", [])))
        active: list[Emiten] = []
        for symbol in symbols:
            emiten = self.session.get(Emiten, symbol) or Emiten(symbol=symbol)
            try:
                body = self.company_overview(symbol)
                overview = body.get("overview") or {}
                emiten.company_name = str(body.get("company_name") or emiten.company_name or "")
                emiten.sector = str(overview.get("sector") or emiten.sector or "")
                emiten.sub_sector = str(overview.get("sub_sector") or emiten.sub_sector or "")
            except Exception as exc:  # noqa: BLE001 - keep the Emiten; name/sector stay as before
                log.warning("company overview %s gagal: %s", symbol, exc)
            emiten.is_excluded = is_financial_sector(emiten.sector or "", emiten.sub_sector or "")
            self.session.add(emiten)
            if not emiten.is_excluded:
                active.append(emiten)
        self.session.flush()
        return active
