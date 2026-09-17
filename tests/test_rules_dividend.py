import json
from datetime import date

import pytest

from afs.domain import Dividend, FindingStatus
from afs.rules.dividend import EarningsWithoutDividend
from tests.fixtures.rules_factory import make_input

rule = EarningsWithoutDividend()
AS_OF = date(2025, 11, 15)


def test_no_dividend_profitable_warning():
    f = rule.evaluate(make_input(as_of=AS_OF, dividends=[]))
    assert f.status == FindingStatus.WARNING
    assert f.value is None
    assert f.headline == "Membukukan laba dan kas operasi positif 12 bulan terakhir, tapi tidak membagikan dividen."
    json.dumps(f.to_dict())


def test_recent_dividend_pass():
    f = rule.evaluate(make_input(as_of=AS_OF, dividends=[Dividend(date(2025, 5, 12), 100.0)]))
    assert f.status == FindingStatus.PASS
    assert f.value == (AS_OF - date(2025, 5, 12)).days
    assert "12 Mei 2025" in f.headline


def test_window_boundaries():
    # window (as_of - 365d, as_of]; as_of - 365 = 2024-11-15
    edge_out = rule.evaluate(make_input(as_of=AS_OF, dividends=[Dividend(date(2024, 11, 15), 1.0)]))
    assert edge_out.status == FindingStatus.WARNING
    assert edge_out.value == 365
    edge_in = rule.evaluate(make_input(as_of=AS_OF, dividends=[Dividend(date(2024, 11, 16), 1.0)]))
    assert edge_in.status == FindingStatus.PASS
    on_as_of = rule.evaluate(make_input(as_of=AS_OF, dividends=[Dividend(AS_OF, 1.0)]))
    assert on_as_of.status == FindingStatus.PASS
    future = rule.evaluate(make_input(as_of=AS_OF, dividends=[Dividend(date(2025, 11, 16), 1.0)]))
    assert future.status == FindingStatus.WARNING


def test_unsorted_dividends_use_latest():
    divs = [Dividend(date(2025, 6, 1), 1.0), Dividend(date(2023, 1, 1), 1.0), Dividend(date(2025, 9, 1), 1.0)]
    f = rule.evaluate(make_input(as_of=AS_OF, dividends=divs))
    assert f.inputs["last_ex_date"] == "2025-09-01"


@pytest.mark.parametrize("field", ["earnings", "operating_cash_flow"])
def test_not_profitable_pass(field):
    f = rule.evaluate(make_input({k: {field: -100.0} for k in range(4)}, as_of=AS_OF, dividends=[]))
    assert f.status == FindingStatus.PASS


def test_never_red_flag():
    f = rule.evaluate(make_input({k: {"earnings": 1e12, "operating_cash_flow": 1e12} for k in range(4)}, dividends=[]))
    assert f.status == FindingStatus.WARNING


def test_dividends_none_insufficient():
    f = rule.evaluate(make_input(dividends=None))
    assert f.status == FindingStatus.INSUFFICIENT_DATA
    assert "corporate actions" in f.missing


def test_ttm_missing_quarter_insufficient():
    f = rule.evaluate(make_input(drop=[2], dividends=[]))
    assert f.status == FindingStatus.INSUFFICIENT_DATA


def test_t4_not_required():
    assert rule.evaluate(make_input(drop=[4], dividends=[])).status == FindingStatus.WARNING
