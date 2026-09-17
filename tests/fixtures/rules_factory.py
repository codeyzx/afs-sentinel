"""Builders for EvaluationInput used by the Forensic Rule tests."""

from __future__ import annotations

from datetime import date
from typing import Any, Sequence

from afs.domain import Dividend, EvaluationInput, Filing, Quarter

REPORT_DATES = [date(2025, 9, 30), date(2025, 6, 30), date(2025, 3, 31), date(2024, 12, 31), date(2024, 9, 30)]

BASE_ROW: dict[str, Any] = {
    "revenue": 1000.0,
    "gross_profit": 300.0,
    "earnings": 100.0,
    "operating_cash_flow": 100.0,
    "ebit": 150.0,
    "operating_pnl": 140.0,
    "total_assets": 2000.0,
    "total_liabilities": 800.0,
    "total_equity": 1200.0,
    "total_current_asset": 900.0,
    "current_liabilities": 500.0,
}


def make_quarters(overrides: dict[int, dict[str, Any]] | None = None, drop: Sequence[int] = ()) -> list[Quarter | None]:
    overrides = overrides or {}
    out: list[Quarter | None] = []
    for k, d in enumerate(REPORT_DATES):
        if k in drop:
            out.append(None)
            continue
        out.append(Quarter(report_date=d, data={**BASE_ROW, **overrides.get(k, {})}))
    return out


def make_input(
    overrides: dict[int, dict[str, Any]] | None = None,
    drop: Sequence[int] = (),
    as_of: date = date(2025, 11, 15),
    filings: Sequence[Filing] | None = (),
    dividends: Sequence[Dividend] | None = (),
    is_backtest: bool = False,
) -> EvaluationInput:
    return EvaluationInput(
        symbol="TEST",
        quarters=make_quarters(overrides, drop),
        as_of=as_of,
        filings=None if filings is None else list(filings),
        dividends=None if dividends is None else list(dividends),
        is_backtest=is_backtest,
    )


def all_quarters(**fields: Any) -> dict[int, dict[str, Any]]:
    return {k: dict(fields) for k in range(5)}
