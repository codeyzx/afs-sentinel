from __future__ import annotations

import json
import re
from datetime import date

from afs.config import get_settings


def test_universe_config_shape():
    data = json.loads(get_settings().universe_path.read_text())
    symbols = data["symbols"]
    assert 25 <= len(symbols) <= 35
    assert len(set(symbols)) == len(symbols)
    assert all(re.fullmatch(r"[A-Z]{4}\.JK", s) for s in symbols)
    assert not {"BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK"} & set(symbols)


def test_backtest_cases_shape():
    cases = json.loads(get_settings().backtest_cases_path.read_text())["cases"]
    assert {c["case_id"] for c in cases} == {"WSKT", "SRIL"}
    for case in cases:
        assert case["symbol"].endswith(".JK") and case["company_name"]
        for event in case["events"]:
            date.fromisoformat(event["date"])
            assert event["label"] and event["source_url"].startswith("https://")
