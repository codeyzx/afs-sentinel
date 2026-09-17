"""Shared helpers for Forensic Rules: quarter access with input capture, formatting, finding builders."""

from __future__ import annotations

from datetime import date
from typing import Any, Mapping

from afs.domain import EvaluationInput, FindingStatus, Quarter, RuleFinding, quarter_label
from afs.labels import RULE_META, RuleMeta

QUARTERLY_ENDPOINT = "/v2/financials/quarterly/{symbol}/"
FILINGS_ENDPOINT = "/v2/filings/?symbol={symbol}"
CORPORATE_ACTIONS_ENDPOINT = "/v2/company/corporate-actions/{symbol}/"

_MONTHS_ID = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def shift_quarter_end(d: date, k: int) -> date:
    """Quarter-end date k quarters before the quarter containing d."""
    idx = d.year * 4 + (d.month - 1) // 3 - k
    year, q = divmod(idx, 4)
    month = (q + 1) * 3
    day = 31 if month in (3, 12) else 30
    return date(year, month, day)


def fmt_num(value: float, decimals: int = 2) -> str:
    """1.4234 -> '1,42' (Indonesian decimal comma)."""
    return f"{value:.{decimals}f}".replace(".", ",")


def fmt_pct(fraction: float, decimals: int = 1) -> str:
    """0.138 -> '13,8%'."""
    return fmt_num(fraction * 100, decimals) + "%"


def fmt_pct_units(value: float) -> str:
    """Percent-unit value trimmed to at most 2 decimals: 4.90 -> '4,9%', 2.0 -> '2%'."""
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text.replace(".", ",") + "%"


def fmt_date_id(d: date) -> str:
    """2026-05-12 -> '12 Mei 2026'."""
    return f"{d.day} {_MONTHS_ID[d.month - 1]} {d.year}"


def fmt_weight(w: float) -> str:
    return str(int(w)) if float(w).is_integer() else fmt_num(w, 1)


class Collector:
    """Reads quarter fields while recording every value used and everything missing."""

    def __init__(self, inp: EvaluationInput) -> None:
        self.inp = inp
        self.values: list[dict[str, Any]] = []
        self._missing: list[str] = []

    def quarter(self, k: int) -> Quarter | None:
        quarters = self.inp.quarters
        return quarters[k] if k < len(quarters) else None

    def add_missing(self, text: str) -> None:
        if text not in self._missing:
            self._missing.append(text)

    def get(self, k: int, field: str) -> float | None:
        q = self.quarter(k)
        if q is None:
            expected = shift_quarter_end(self.inp.report_date, k)
            self.add_missing(f"laporan kuartal {quarter_label(expected)} tidak tersedia")
            return None
        value = q.get(field)
        self.values.append({"field": field, "report_date": q.report_date.isoformat(), "value": value})
        if value is None:
            self.add_missing(f"{field} kuartal {quarter_label(q.report_date)} kosong")
        return value

    def ttm(self, field: str) -> float | None:
        vals = [self.get(k, field) for k in range(4)]
        if any(v is None for v in vals):
            return None
        return float(sum(v for v in vals if v is not None))

    @property
    def missing(self) -> str | None:
        return "; ".join(self._missing) if self._missing else None


def base_inputs(
    values: list[dict[str, Any]], formula: str, endpoint: str, note: str | None = None, **extra: Any
) -> dict[str, Any]:
    return {"values": values, "formula": formula, "endpoint": endpoint, "note": note, **extra}


def insufficient(
    rule_id: str, thresholds: Mapping[str, Any], inputs: Mapping[str, Any], missing: str
) -> RuleFinding:
    return RuleFinding(
        rule_id=rule_id,
        status=FindingStatus.INSUFFICIENT_DATA,
        value=None,
        thresholds=dict(thresholds),
        inputs=dict(inputs),
        headline=f"Tak bisa dinilai: {missing}",
        missing=missing,
    )


class BaseRule:
    """Display metadata comes from afs.labels.RULE_META (single source of truth)."""

    rule_id: str = ""

    def __init__(self) -> None:
        meta: RuleMeta = RULE_META[self.rule_id]
        self.name = meta.name
        self.subtitle = meta.subtitle
        self.weight = meta.weight
        self.is_core = meta.is_core

    def evaluate(self, inp: EvaluationInput) -> RuleFinding:  # pragma: no cover - abstract
        raise NotImplementedError
