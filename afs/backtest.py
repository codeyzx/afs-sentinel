"""Backtest engine (docs/system-rules.md §8).

    uv run python -m afs.backtest --dry-run          # estimate quarterly credits, fetch nothing paid
    uv run python -m afs.backtest [--case WSKT ...]  # evaluate every quarter from 2021-Q1

For each Backtest case and each Report Period t >= 2021-03-31 the six Forensic Rules run as if
today were report_date t. Results are upserted into models.BacktestResult (case_id + report_date).
A Backtest creates no Incident and sends no Telegram message.
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from afs import db
from afs.config import get_settings
from afs.domain import Severity, quarter_label
from afs.models import ApiCache, BacktestResult, utcnow
from afs.rules import evaluate_all
from afs.scoring import compute_score
from afs.sectors.client import SectorsClient
from afs.sectors.repository import WINDOW, DataRepository, _today_wib, quarter_end_before
from afs.web.backtest_view import BacktestCase, claim_sentence, load_cases

log = logging.getLogger(__name__)

BACKTEST_START = date(2021, 3, 31)  # 2021-Q1 needs t-4 = 2020-Q1, the first quarter the API has


@dataclass
class CaseSummary:
    case_id: str
    symbol: str
    quarters_evaluated: int = 0
    first_moderate: date | None = None
    first_critical: date | None = None
    credits_used: int = 0
    claims: list[str] = field(default_factory=list)  # one claim sentence per real-world event
    error: str | None = None


# ---------------------------------------------------------------- config


def select_cases(case_ids: list[str] | None = None, path: Path | None = None) -> list[BacktestCase]:
    """Cases from config/backtest_cases.json, optionally narrowed to case_ids (unknown id -> ValueError)."""
    cases = load_cases(path or get_settings().backtest_cases_path)
    if not case_ids:
        return cases
    by_id = {c.case_id.upper(): c for c in cases}
    unknown = [cid for cid in case_ids if cid.upper() not in by_id]
    if unknown:
        raise ValueError(f"Kasus tidak dikenal: {', '.join(unknown)} (tersedia: {', '.join(by_id) or '-'})")
    return [by_id[cid.upper()] for cid in dict.fromkeys(case_ids)]


def _report_dates(repo: DataRepository, symbol: str, start: date) -> list[date]:
    return [d for d in repo.available_report_dates(symbol) if d >= start]


# ---------------------------------------------------------------- credit estimate


def estimate_credits(
    session: Session,
    client: SectorsClient,
    case_ids: list[str] | None = None,
    *,
    start: date = BACKTEST_START,
    cases_path: Path | None = None,
    today: Callable[[], date] = _today_wib,
) -> dict[str, int]:
    """Quarterly rows (1 credit each) a Backtest would still fetch, per case.

    Mirrors DataRepository._quarter: a quarter in the t..t-4 window costs a credit only when it is not
    cached (kind="quarter") and the API lists it (or it is t itself). Only the free dates endpoint is called.
    """
    repo = DataRepository(session, client, today=today)
    out: dict[str, int] = {}
    for case in select_cases(case_ids, cases_path):
        report_dates = _report_dates(repo, case.symbol, start)
        known = set(repo.available_report_dates(case.symbol))
        cached = set(
            session.scalars(
                select(ApiCache.key).where(ApiCache.kind == "quarter", ApiCache.symbol == case.symbol)
            )
        )
        needed: set[date] = set()
        for t in report_dates:
            for k in range(WINDOW):
                d = quarter_end_before(t, k)
                if d.isoformat() not in cached and (d in known or d == t):
                    needed.add(d)
        out[case.case_id] = len(needed)
    return out


# ---------------------------------------------------------------- run


def _upsert(session: Session, case: BacktestCase, report_date: date, findings, score) -> BacktestResult:
    row = session.scalar(
        select(BacktestResult).where(BacktestResult.case_id == case.case_id, BacktestResult.report_date == report_date)
    ) or BacktestResult(case_id=case.case_id, report_date=report_date)
    row.symbol = case.symbol
    row.score = score.score
    row.severity = score.severity.value if score.severity else None
    row.low_confidence = score.low_confidence
    row.severity_reason = score.severity_reason
    row.findings = [f.to_dict() for f in findings]
    row.computed_at = utcnow()
    session.add(row)
    return row


def _first_at_least(rows: list[BacktestResult], level: Severity) -> date | None:
    for r in sorted(rows, key=lambda r: r.report_date):
        if r.severity and Severity(r.severity).rank >= level.rank:
            return r.report_date
    return None


def run_case(
    session: Session, repo: DataRepository, case: BacktestCase, *, start: date = BACKTEST_START
) -> CaseSummary:
    summary = CaseSummary(case_id=case.case_id, symbol=case.symbol)
    credits_before = repo.client.credits_used
    try:
        for report_date in _report_dates(repo, case.symbol, start):
            inp = repo.build_backtest_input(case.symbol, report_date)
            if inp.quarters[0] is None:
                log.warning("%s %s: kuartal t tidak tersedia, dilewati", case.case_id, report_date)
                session.commit()  # keep the negative cache entry
                continue
            findings = evaluate_all(inp)
            _upsert(session, case, report_date, findings, compute_score(findings))
            session.commit()  # after every quarter, so paid-for cache rows persist
            summary.quarters_evaluated += 1
    except Exception as exc:  # noqa: BLE001 - one failing case must not lose the others
        session.rollback()
        log.exception("backtest %s gagal", case.case_id)
        summary.error = str(exc)
    finally:
        summary.credits_used = repo.client.credits_used - credits_before

    rows = list(
        session.scalars(
            select(BacktestResult)
            .where(BacktestResult.case_id == case.case_id, BacktestResult.report_date >= start)
            .order_by(BacktestResult.report_date)
        )
    )
    summary.first_moderate = _first_at_least(rows, Severity.MODERATE)
    summary.first_critical = _first_at_least(rows, Severity.CRITICAL)
    summary.claims = [f"{e.date.isoformat()} {e.label}: {claim_sentence(rows, e)}" for e in case.events]
    return summary


def run_backtest(
    session: Session,
    client: SectorsClient,
    *,
    case_ids: list[str] | None = None,
    start: date = BACKTEST_START,
    cases_path: Path | None = None,
    today: Callable[[], date] = _today_wib,
) -> list[CaseSummary]:
    """Evaluate every configured case; commits on `session` after each quarter."""
    repo = DataRepository(session, client, today=today)
    return [run_case(session, repo, case, start=start) for case in select_cases(case_ids, cases_path)]


# ---------------------------------------------------------------- CLI


def _fmt(d: date | None) -> str:
    return quarter_label(d) if d else "-"


def format_summaries(summaries: list[CaseSummary]) -> str:
    lines = [f"{'Kasus':<8} {'Kuartal':>7} {'Sedang':>8} {'Kritis':>8} {'Kredit':>6}"]
    for s in summaries:
        lines.append(
            f"{s.case_id:<8} {s.quarters_evaluated:>7} {_fmt(s.first_moderate):>8} "
            f"{_fmt(s.first_critical):>8} {s.credits_used:>6}"
        )
    for s in summaries:
        if s.error:
            lines.append(f"{s.case_id}: GAGAL — {s.error}")
        for claim in s.claims:
            lines.append(f"{s.case_id}: {claim}")
    return "\n".join(lines)


def main(argv: list[str] | None = None, *, client: SectorsClient | None = None) -> int:
    parser = argparse.ArgumentParser(description="Jalankan Backtest (docs/system-rules.md §8)")
    parser.add_argument("--case", action="append", dest="cases", metavar="ID", help="hanya kasus ini (bisa diulang)")
    parser.add_argument("--dry-run", action="store_true", help="hanya perkiraan kredit, tanpa mengambil kuartal")
    args = parser.parse_args(argv)

    db.init_db()
    client = client or SectorsClient()
    try:
        with db.session_scope() as session:
            estimate = estimate_credits(session, client, args.cases)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    print("Perkiraan kredit kuartal: " + ", ".join(f"{k}={v}" for k, v in estimate.items()))
    print(f"Total: {sum(estimate.values())}")
    if args.dry_run:
        return 0

    started = datetime.now()
    with db.session_scope() as session:
        summaries = run_backtest(session, client, case_ids=args.cases)
    print(format_summaries(summaries))
    print(f"Selesai dalam {(datetime.now() - started).total_seconds():.1f} dtk")
    return 1 if any(s.error for s in summaries) else 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main(sys.argv[1:]))
