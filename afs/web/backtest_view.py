"""Backtest page data: case config + automatic claim sentence (docs/system-rules.md §8)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Sequence

from afs.domain import Severity, quarter_label


@dataclass(frozen=True)
class CaseEvent:
    date: date
    label: str
    source_url: str = ""
    verified: bool | None = None


@dataclass(frozen=True)
class BacktestCase:
    case_id: str
    symbol: str
    company_name: str
    events: list[CaseEvent] = field(default_factory=list)


def load_cases(path: Path) -> list[BacktestCase]:
    """Missing or malformed config -> no cases (the page shows its empty state)."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    cases: list[BacktestCase] = []
    for c in raw.get("cases", []) if isinstance(raw, dict) else []:
        try:
            events = [
                CaseEvent(
                    date=date.fromisoformat(e["date"]),
                    label=e.get("label", ""),
                    source_url=e.get("source_url", ""),
                    verified=e.get("verified"),
                )
                for e in c.get("events", [])
            ]
            cases.append(
                BacktestCase(
                    case_id=c["case_id"],
                    symbol=c.get("symbol", c["case_id"]),
                    company_name=c.get("company_name", ""),
                    events=sorted(events, key=lambda e: e.date),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return cases


def months_between(start: date, end: date) -> int:
    """Whole calendar months from start to end (a partial month is not counted)."""
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    return months


def claim_sentence(results: Sequence[Any], event: CaseEvent) -> str:
    """results: objects with report_date and severity (BacktestResult rows), any order."""
    for r in sorted(results, key=lambda r: r.report_date):
        if r.report_date >= event.date:
            break
        if r.severity and Severity(r.severity).rank >= Severity.MODERATE.rank:
            n = months_between(r.report_date, event.date)
            return f"Pertama kali Sedang: {quarter_label(r.report_date)}, {n} bulan sebelum {event.label}"
    return "Tidak terdeteksi lebih awal"
