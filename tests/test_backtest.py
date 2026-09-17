from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import httpx
import pytest
from sqlalchemy import func, select

from afs import backtest
from afs.db import session_scope
from afs.domain import FindingStatus
from afs.models import ApiCache, BacktestResult, Incident, IncidentEvent
from afs.sectors.client import SectorsClient

FIX = Path(__file__).parent / "fixtures"
WSKT_ROW = json.loads((FIX / "sectors_quarter_WSKT_2021-12-31.json").read_text())[0]
QUARTERS = ["2020-03-31", "2020-06-30", "2020-09-30", "2020-12-31", "2021-03-31", "2021-06-30", "2021-09-30", "2021-12-31"]
TODAY = lambda: date(2026, 9, 19)  # noqa: E731


class FakeApi:
    def __init__(self, quarters: list[str]):
        self.quarters = quarters
        self.requests: list[httpx.Request] = []

    def __call__(self, req: httpx.Request) -> httpx.Response:
        self.requests.append(req)
        path = req.url.path
        if "get_quarterly_financial_dates" in path:
            out: dict[str, list] = {}
            for iso in self.quarters:
                out.setdefault(iso[:4], []).append([iso, "q"])
            return httpx.Response(200, json=out)
        if path.startswith("/v2/financials/quarterly/"):
            wanted = req.url.params["report_date"]
            return httpx.Response(200, json=[{**WSKT_ROW, "date": wanted}], headers={"limit-consumption": "1"})
        if "corporate-actions" in path:
            return httpx.Response(200, json={"corporate_actions": {"dividend": None}})
        return httpx.Response(404)

    def count(self, marker: str) -> int:
        return sum(marker in str(r.url) for r in self.requests)


@pytest.fixture
def api():
    return FakeApi(QUARTERS)


@pytest.fixture
def client(api):
    http = httpx.Client(transport=httpx.MockTransport(api))
    return SectorsClient("k", base_url="https://api.test", http=http, sleep=lambda _: None)


@pytest.fixture
def cases_path(tmp_path, monkeypatch):
    path = tmp_path / "backtest_cases.json"
    path.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "case_id": "WSKT",
                        "symbol": "WSKT.JK",
                        "company_name": "Waskita Karya",
                        "events": [{"date": "2023-05-08", "label": "suspensi BEI"}],
                    }
                ]
            }
        )
    )
    from afs.config import get_settings

    monkeypatch.setattr(get_settings(), "backtest_cases_path", path)
    return path


def run(client, cases_path, **kw):
    with session_scope() as s:
        return backtest.run_backtest(s, client, cases_path=cases_path, today=TODAY, **kw)


def test_run_evaluates_each_quarter_from_start(engine, client, api, cases_path):
    (summary,) = run(client, cases_path)
    assert summary.case_id == "WSKT" and summary.error is None
    assert summary.quarters_evaluated == 4
    assert summary.credits_used == 8
    assert len(summary.claims) == 1 and "suspensi BEI" in summary.claims[0]
    with session_scope() as s:
        rows = s.scalars(select(BacktestResult).order_by(BacktestResult.report_date)).all()
        assert [r.report_date.isoformat() for r in rows] == QUARTERS[4:]
        assert all(r.symbol == "WSKT.JK" and len(r.findings) == 6 for r in rows)


def test_running_twice_does_not_duplicate_or_refetch(engine, client, api, cases_path):
    run(client, cases_path)
    fetched = api.count("/financials/quarterly/")
    (again,) = run(client, cases_path)
    assert api.count("/financials/quarterly/") == fetched
    assert again.credits_used == 0 and again.quarters_evaluated == 4
    with session_scope() as s:
        assert s.scalar(select(func.count()).select_from(BacktestResult)) == 4


def test_insider_is_always_insufficient_data(engine, client, api, cases_path):
    run(client, cases_path)
    with session_scope() as s:
        for r in s.scalars(select(BacktestResult)):
            insider = [f for f in r.findings if f["rule_id"] == "INSIDER_SELLING"]
            assert insider and insider[0]["status"] == FindingStatus.INSUFFICIENT_DATA.value
    assert api.count("/filings/") == 0


def test_creates_no_incidents(engine, client, cases_path):
    run(client, cases_path)
    with session_scope() as s:
        assert s.scalar(select(func.count()).select_from(Incident)) == 0
        assert s.scalar(select(func.count()).select_from(IncidentEvent)) == 0


def test_first_severity_matches_rows(engine, client, cases_path):
    (summary,) = run(client, cases_path)
    with session_scope() as s:
        rows = s.scalars(select(BacktestResult).order_by(BacktestResult.report_date)).all()
    flagged = [r.report_date for r in rows if r.severity in ("MODERATE", "CRITICAL")]
    assert summary.first_moderate == (flagged[0] if flagged else None)


def test_estimate_counts_uncached_quarters_without_paid_calls(engine, client, api, cases_path):
    with session_scope() as s:
        assert backtest.estimate_credits(s, client, None, cases_path=cases_path, today=TODAY) == {"WSKT": 8}
    assert api.count("/financials/quarterly/") == 0 and client.credits_used == 0

    with session_scope() as s:
        for iso in QUARTERS[:3]:
            s.add(ApiCache(kind="quarter", symbol="WSKT.JK", key=iso, payload={"missing": True}))
    with session_scope() as s:
        assert backtest.estimate_credits(s, client, ["wskt"], cases_path=cases_path, today=TODAY) == {"WSKT": 5}

    run(client, cases_path)
    with session_scope() as s:
        assert backtest.estimate_credits(s, client, None, cases_path=cases_path, today=TODAY) == {"WSKT": 0}


def test_estimate_skips_quarters_the_api_does_not_list(engine, cases_path):
    api = FakeApi(QUARTERS[2:])  # 2020-Q1/Q2 not listed -> never fetched
    http = httpx.Client(transport=httpx.MockTransport(api))
    client = SectorsClient("k", base_url="https://api.test", http=http, sleep=lambda _: None)
    with session_scope() as s:
        assert backtest.estimate_credits(s, client, None, cases_path=cases_path, today=TODAY) == {"WSKT": 6}
    (summary,) = run(client, cases_path)
    assert summary.credits_used == 6


def test_unknown_case_raises(engine, client, cases_path):
    with pytest.raises(ValueError):
        run(client, cases_path, case_ids=["AISA"])


def test_cli_dry_run_fetches_no_quarters(engine, client, api, cases_path, capsys):
    assert backtest.main(["--dry-run"], client=client) == 0
    out = capsys.readouterr().out
    assert "WSKT=8" in out
    assert api.count("/financials/quarterly/") == 0
    with session_scope() as s:
        assert s.scalar(select(func.count()).select_from(BacktestResult)) == 0


def test_cli_run_prints_table_and_claims(engine, client, cases_path, capsys):
    assert backtest.main(["--case", "WSKT"], client=client) == 0
    out = capsys.readouterr().out
    assert "WSKT" in out and "suspensi BEI" in out


def test_cli_unknown_case_exits_2(engine, client, cases_path):
    assert backtest.main(["--case", "NOPE", "--dry-run"], client=client) == 2
