from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

from afs.db import session_scope
from afs.models import ApiCache, Emiten
from afs.sectors.client import SectorsClient
from afs.sectors.repository import DataRepository, parse_dividends, parse_filings, quarter_end_before

FIX = Path(__file__).parent / "fixtures"


def load(name: str):
    return json.loads((FIX / name).read_text())


class FakeApi:
    """Routes Sectors API paths to canned data and records every request."""

    def __init__(self, *, dates: dict, quarters: dict[str, dict | None], **extra):
        self.dates = dates
        self.quarters = quarters  # report_date ISO -> row (None = API returns a later quarter)
        self.filings = extra.get("filings", {"results": [], "pagination": {"has_next": False}})
        self.corporate_actions = extra.get("corporate_actions", {"symbol": "X", "corporate_actions": {"dividend": None}})
        self.companies = extra.get("companies", {})
        self.fail = set(extra.get("fail", ()))
        self.requests: list[httpx.Request] = []

    def __call__(self, req: httpx.Request) -> httpx.Response:
        self.requests.append(req)
        path = req.url.path
        for marker in self.fail:
            if marker in path:
                return httpx.Response(404)
        if "get_quarterly_financial_dates" in path:
            return httpx.Response(200, json=self.dates)
        if path.startswith("/v2/financials/quarterly/"):
            wanted = req.url.params["report_date"]
            row = self.quarters.get(wanted)
            if row is None:
                return httpx.Response(200, json=[{"date": "2099-03-31"}], headers={"limit-consumption": "1"})
            return httpx.Response(200, json=[{**row, "date": wanted}], headers={"limit-consumption": "1"})
        if path.startswith("/v2/filings/"):
            return httpx.Response(200, json=self.filings)
        if "corporate-actions" in path:
            return httpx.Response(200, json=self.corporate_actions)
        if path.startswith("/v2/company/report/"):
            symbol = path.split("/")[4]
            return httpx.Response(200, json=self.companies[symbol], headers={"limit-consumption": "1"})
        return httpx.Response(404)

    def count(self, marker: str) -> int:
        return sum(marker in str(r.url) for r in self.requests)


def make_repo(session, api: FakeApi) -> DataRepository:
    http = httpx.Client(transport=httpx.MockTransport(api))
    client = SectorsClient("k", base_url="https://api.test", http=http, sleep=lambda _: None)
    return DataRepository(session, client, today=lambda: date(2026, 9, 19))


def dates_payload(*isos: str) -> dict:
    out: dict[str, list] = {}
    for iso in isos:
        out.setdefault(iso[:4], []).append([iso, "q"])
    return out


def row(earnings: float, ocf: float) -> dict:
    return {"earnings": earnings, "operating_cash_flow": ocf, "total_assets": 1000}


FIVE = ["2025-06-30", "2025-09-30", "2025-12-31", "2026-03-31", "2026-06-30"]


def test_quarter_end_before():
    assert quarter_end_before(date(2026, 6, 30), 0) == date(2026, 6, 30)
    assert quarter_end_before(date(2026, 6, 30), 1) == date(2026, 3, 31)
    assert quarter_end_before(date(2026, 3, 31), 1) == date(2025, 12, 31)
    assert quarter_end_before(date(2026, 3, 31), 4) == date(2025, 3, 31)
    assert quarter_end_before(date(2025, 9, 30), 3) == date(2024, 12, 31)


def test_live_input_second_build_makes_no_http_calls(engine):
    api = FakeApi(dates=dates_payload(*FIVE), quarters={d: row(10, 5) for d in FIVE})
    with session_scope() as s:
        repo = make_repo(s, api)
        inp = repo.build_live_input("ASII.JK", date(2026, 9, 19))
        assert inp is not None
        assert [q.report_date.isoformat() for q in inp.quarters] == FIVE[::-1]
        assert inp.filings == [] and inp.dividends == []
        assert not inp.is_backtest
        assert repo.client.credits_used == 5
        first = len(api.requests)
        again = repo.build_live_input("ASII.JK", date(2026, 9, 19))
        assert again is not None and len(api.requests) == first


def test_new_day_refetches_only_dates_filings_and_actions(engine):
    api = FakeApi(dates=dates_payload(*FIVE), quarters={d: row(10, 5) for d in FIVE})
    with session_scope() as s:
        repo = make_repo(s, api)
        repo.build_live_input("ASII.JK", date(2026, 9, 19))
        before = api.count("/financials/quarterly/")
        repo.build_live_input("ASII.JK", date(2026, 9, 26))
        assert api.count("/financials/quarterly/") == before
        assert api.count("get_quarterly_financial_dates") == 2
        assert api.count("/filings/") == 2


def test_negative_cache_is_never_refetched(engine):
    quarters = {d: row(10, 5) for d in FIVE}
    quarters["2025-12-31"] = None  # listed, but API silently returns a later quarter
    api = FakeApi(dates=dates_payload(*FIVE), quarters=quarters)
    with session_scope() as s:
        repo = make_repo(s, api)
        inp = repo.build_live_input("ASII.JK", date(2026, 9, 19))
        assert inp is not None and inp.quarters[2] is None
        cached = s.query(ApiCache).filter_by(kind="quarter", key="2025-12-31").one()
        assert cached.payload == {"missing": True}
        before = api.count("report_date=2025-12-31")
        repo.build_live_input("ASII.JK", date(2026, 9, 26))
        assert api.count("report_date=2025-12-31") == before == 1


def test_gap_in_dates_list_keeps_positions(engine):
    listed = ["2025-06-30", "2025-09-30", "2026-03-31", "2026-06-30"]  # 2025-12-31 absent
    api = FakeApi(dates=dates_payload(*listed), quarters={d: row(10, 5) for d in listed})
    with session_scope() as s:
        inp = make_repo(s, api).build_live_input("GIAA.JK", date(2026, 9, 19))
    assert inp is not None
    got = [q.report_date.isoformat() if q else None for q in inp.quarters]
    assert got == ["2026-06-30", "2026-03-31", None, "2025-09-30", "2025-06-30"]
    assert api.count("report_date=2025-12-31") == 0


def test_live_uses_latest_date_not_after_as_of(engine):
    api = FakeApi(dates=dates_payload(*FIVE), quarters={d: row(10, 5) for d in FIVE})
    with session_scope() as s:
        inp = make_repo(s, api).build_live_input("ASII.JK", date(2026, 5, 1))
    assert inp is not None and inp.report_date == date(2026, 3, 31)
    assert inp.quarters[4] is None  # 2025-03-31 not listed


def test_live_none_when_no_dates_or_t_missing(engine):
    with session_scope() as s:
        assert make_repo(s, FakeApi(dates={}, quarters={})).build_live_input("X.JK", date(2026, 9, 19)) is None
        api = FakeApi(dates=dates_payload(*FIVE), quarters={d: row(1, 1) for d in FIVE[:-1]} | {FIVE[-1]: None})
        assert make_repo(s, api).build_live_input("Y.JK", date(2026, 9, 19)) is None


def test_live_filings_and_dividend_failures_become_none(engine):
    api = FakeApi(dates=dates_payload(*FIVE), quarters={d: row(1, 1) for d in FIVE}, fail=["/filings/", "corporate-actions"])
    with session_scope() as s:
        inp = make_repo(s, api).build_live_input("ASII.JK", date(2026, 9, 19))
    assert inp is not None and inp.filings is None and inp.dividends is None


def test_live_parses_real_filings_and_dividends(engine):
    api = FakeApi(
        dates=dates_payload(*FIVE),
        quarters={d: row(1, 1) for d in FIVE},
        filings=load("sectors_filings_BUMI_p2.json"),
        corporate_actions=load("sectors_corporate_actions_ASII.json"),
    )
    with session_scope() as s:
        inp = make_repo(s, api).build_live_input("ASII.JK", date(2026, 9, 19))
    assert inp is not None and inp.filings and inp.dividends
    assert all(f.timestamp.tzinfo is not None for f in inp.filings)
    ex_dates = [d.ex_date for d in inp.dividends]
    assert ex_dates == sorted(ex_dates)


def test_backtest_input_filters_dividends_and_caches_actions(engine):
    quarters = ["2020-12-31", "2021-03-31", "2021-06-30", "2021-09-30", "2021-12-31", "2022-03-31"]
    actions = {
        "symbol": "WSKT.JK",
        "corporate_actions": {
            "dividend": [
                {"ex_date": "2022-05-10", "dividend_amount": 5},
                {"ex_date": "2021-05-10", "dividend_amount": 3},
            ]
        },
    }
    api = FakeApi(dates=dates_payload(*quarters), quarters={d: row(1, 1) for d in quarters}, corporate_actions=actions)
    with session_scope() as s:
        repo = make_repo(s, api)
        inp = repo.build_backtest_input("WSKT.JK", date(2021, 12, 31))
        assert inp.is_backtest and inp.filings is None and inp.as_of == date(2021, 12, 31)
        assert [d.ex_date for d in inp.dividends] == [date(2021, 5, 10)]
        repo.build_backtest_input("WSKT.JK", date(2022, 3, 31))
        assert api.count("corporate-actions") == 1
        assert api.count("/filings/") == 0
        assert repo.available_report_dates("WSKT.JK")[-1] == date(2022, 3, 31)


def test_quarters_for_chart_reads_cache_only(engine):
    api = FakeApi(dates=dates_payload(*FIVE), quarters={d: row(i, -i) for i, d in enumerate(FIVE)})
    with session_scope() as s:
        repo = make_repo(s, api)
        repo.build_live_input("ASII.JK", date(2026, 9, 19))
        n = len(api.requests)
        chart = repo.quarters_for_chart("ASII.JK", date(2026, 6, 30))
        assert len(api.requests) == n
        assert chart[0] == (date(2025, 6, 30), 0.0, 0.0)
        assert chart[-1] == (date(2026, 6, 30), 4.0, -4.0)
        assert repo.quarters_for_chart("ASII.JK", date(2026, 9, 30))[-1] == (date(2026, 9, 30), None, None)


def test_sync_universe_excludes_financials(engine, tmp_path):
    universe = tmp_path / "universe.json"
    universe.write_text(json.dumps({"symbols": ["ASII.JK", "BBCA.JK", "asii.jk"]}))
    companies = {
        "ASII.JK": load("sectors_company_ASII.json"),
        "BBCA.JK": {"company_name": "Bank Central Asia Tbk", "overview": {"sector": "Financials", "sub_sector": "Banks"}},
    }
    api = FakeApi(dates={}, quarters={}, companies=companies)
    with session_scope() as s:
        repo = make_repo(s, api)
        active = repo.sync_universe(universe)
        assert [e.symbol for e in active] == ["ASII.JK"]
        assert active[0].company_name == "Astra International Tbk"
        assert active[0].sector == "Industrials"
        assert s.get(Emiten, "BBCA.JK").is_excluded
        repo.sync_universe(universe)
        assert api.count("/company/report/") == 2


def test_parse_helpers_tolerate_bad_rows():
    filings = parse_filings(
        [
            {"timestamp": "2026-06-19T09:23:00", "transaction_type": "sell", "holder_type": "insider"},
            {"timestamp": "2026-06-19T02:23:00Z", "transaction_type": "buy"},
            {"timestamp": None},
            "junk",
        ]
    )
    assert len(filings) == 2
    assert filings[0].timestamp.utcoffset() == timedelta(hours=7)
    assert filings[1].timestamp == datetime(2026, 6, 19, 2, 23, tzinfo=timezone.utc)
    assert filings[0].share_percentage_transaction is None
    assert parse_dividends({"corporate_actions": None}) == []
    assert parse_dividends({"corporate_actions": {"dividend": [{"ex_date": None}]}}) == []


@pytest.mark.parametrize("sector,excluded", [("Financials", True), ("Industrials", False)])
def test_financial_marker(sector, excluded):
    from afs.sectors.repository import is_financial_sector

    assert is_financial_sector(sector, "") is excluded
