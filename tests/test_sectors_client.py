from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import httpx
import pytest

from afs.sectors.client import SectorsApiError, SectorsClient

FIX = Path(__file__).parent / "fixtures"


def load(name: str):
    return json.loads((FIX / name).read_text())


def make_client(handler) -> tuple[SectorsClient, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def wrapped(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    http = httpx.Client(transport=httpx.MockTransport(wrapped))
    return SectorsClient("test-key", base_url="https://api.test", http=http, sleep=lambda _: None), seen


def test_quarterly_returns_matching_row_and_counts_credits():
    row = load("sectors_quarter_WSKT_2021-12-31.json")

    def handler(req):
        assert req.headers["Authorization"] == "test-key"
        assert req.url.params["report_date"] == "2021-12-31"
        return httpx.Response(200, json=row, headers={"limit-consumption": "1"})

    client, _ = make_client(handler)
    got = client.quarterly("WSKT.JK", date(2021, 12, 31))
    assert got is not None and got["date"] == "2021-12-31"
    assert client.credits_used == 1


def test_quarterly_date_mismatch_is_none():
    # API returns 2020-03-31 when 2019-12-31 is requested
    row = load("sectors_quarter_WSKT_2021-12-31.json")
    row[0]["date"] = "2022-03-31"
    client, _ = make_client(lambda req: httpx.Response(200, json=row, headers={"limit-consumption": "1"}))
    assert client.quarterly("WSKT.JK", date(2021, 12, 31)) is None
    assert client.credits_used == 1


def test_quarterly_empty_is_none():
    client, _ = make_client(lambda req: httpx.Response(200, json=[]))
    assert client.quarterly("WSKT.JK", date(2021, 12, 31)) is None
    assert client.credits_used == 0


def test_filings_follows_pagination():
    p1, p2 = load("sectors_filings_BUMI_p1.json"), load("sectors_filings_BUMI_p2.json")

    def handler(req):
        return httpx.Response(200, json=p2 if req.url.params.get("offset") == "20" else p1)

    client, seen = make_client(handler)
    rows = client.filings("BUMI.JK")
    assert len(rows) == 26
    assert len(seen) == 2


def test_filings_page_cap():
    page = {"results": [{"x": 1}], "pagination": {"has_next": True, "next_offset": 20}}
    client, seen = make_client(lambda req: httpx.Response(200, json=page))
    assert len(client.filings("BUMI.JK")) == 10
    assert len(seen) == 10


def test_retries_on_5xx_then_succeeds():
    calls = iter([httpx.Response(503), httpx.Response(429), httpx.Response(200, json={"symbol": "ASII.JK"})])
    client, seen = make_client(lambda req: next(calls))
    assert client.corporate_actions("ASII.JK") == {"symbol": "ASII.JK"}
    assert len(seen) == 3


def test_gives_up_after_two_retries():
    client, seen = make_client(lambda req: httpx.Response(500))
    with pytest.raises(SectorsApiError):
        client.company_overview("ASII.JK")
    assert len(seen) == 3


def test_4xx_not_retried():
    client, seen = make_client(lambda req: httpx.Response(404, json={"details": "nope"}))
    with pytest.raises(SectorsApiError):
        client.quarterly_dates("ASII.JK")
    assert len(seen) == 1


def test_quarterly_dates_and_overview_parse():
    def handler(req):
        if "get_quarterly_financial_dates" in req.url.path:
            return httpx.Response(200, json=load("sectors_dates_WSKT.json"))
        assert req.url.params["sections"] == "overview"
        return httpx.Response(200, json=load("sectors_company_ASII.json"), headers={"limit-consumption": "1"})

    client, _ = make_client(handler)
    assert client.quarterly_dates("WSKT.JK")["2026"][-1] == ["2026-06-30", "q2"]
    assert client.company_overview("ASII.JK")["overview"]["sector"] == "Industrials"
    assert client.credits_used == 1


def test_rate_limit_waits_long_and_honours_retry_after():
    calls = iter([
        httpx.Response(429, json={"error": "RATE_LIMIT_EXCEEDED"}),
        httpx.Response(429, headers={"retry-after": "7"}),
        httpx.Response(200, json={"symbol": "ASII.JK"}),
    ])
    waits = []
    http = httpx.Client(transport=httpx.MockTransport(lambda req: next(calls)))
    client = SectorsClient("k", base_url="https://api.test", http=http, sleep=waits.append, min_interval=0)
    assert client.corporate_actions("ASII.JK") == {"symbol": "ASII.JK"}
    assert waits == [20.0, 7.0]


def test_rate_limit_gives_up_after_budget():
    http = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(429)))
    client = SectorsClient("k", base_url="https://api.test", http=http, sleep=lambda _: None, rate_limit_retries=2)
    with pytest.raises(SectorsApiError):
        client.corporate_actions("ASII.JK")


def test_requests_are_spaced_by_min_interval():
    now = [100.0]
    waits = []

    def sleep(s):
        waits.append(round(s, 2))
        now[0] += s

    http = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, json={})))
    client = SectorsClient("k", base_url="https://api.test", http=http, sleep=sleep, clock=lambda: now[0], min_interval=1.5)
    client.corporate_actions("A.JK")
    now[0] += 0.5
    client.corporate_actions("B.JK")
    assert waits == [1.0]
