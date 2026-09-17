import json

import pytest

from afs.domain import FindingStatus
from afs.rules.altman import AltmanZAdapted, classify
from tests.fixtures.rules_factory import make_input

rule = AltmanZAdapted()


@pytest.mark.parametrize(
    "z,expected",
    [
        (1.7999, FindingStatus.RED_FLAG),
        (1.8, FindingStatus.WARNING),
        (2.8999, FindingStatus.WARNING),
        (2.9, FindingStatus.PASS),
        (-3.0, FindingStatus.RED_FLAG),
    ],
)
def test_classify_boundaries(z, expected):
    assert classify(z) == expected


def test_base_case_value():
    # X1=(900-500)/2000=0.2, X2=1200/2000=0.6, X3=600/2000=0.3, X4=1200/800=1.5
    f = rule.evaluate(make_input())
    expected = 6.56 * 0.2 + 3.26 * 0.6 + 6.72 * 0.3 + 1.05 * 1.5
    assert f.value == pytest.approx(expected)
    assert f.status == FindingStatus.PASS
    assert f.inputs["components"]["X4"] == pytest.approx(1.5)
    assert f.inputs["fallback_used"] is False
    assert "laba ditahan" in f.inputs["note"]
    json.dumps(f.to_dict())


def test_red_flag_headline():
    overrides = {0: {"total_current_asset": 300.0, "current_liabilities": 900.0, "total_equity": 200.0,
                     "total_liabilities": 1800.0, "ebit": 10.0}}
    overrides.update({k: {"ebit": 10.0} for k in (1, 2, 3)})
    f = rule.evaluate(make_input(overrides))
    assert f.status == FindingStatus.RED_FLAG
    assert f.headline.startswith("Skor Altman ")
    assert "masuk zona kesulitan keuangan" in f.headline
    assert "," in f.headline.split(" — ")[0]


def test_operating_pnl_fallback_recorded():
    f = rule.evaluate(make_input({2: {"ebit": None}}))
    assert f.status != FindingStatus.INSUFFICIENT_DATA
    assert f.inputs["fallback_used"] is True
    assert f.inputs["ttm_ebit"] == pytest.approx(150 * 3 + 140)
    fallback = [s for s in f.inputs["ebit_sources"] if s["fallback"]]
    assert fallback == [{"report_date": "2025-03-31", "source": "operating_pnl", "fallback": True}]


def test_both_ebit_and_pnl_null_insufficient():
    f = rule.evaluate(make_input({1: {"ebit": None, "operating_pnl": None}}))
    assert f.status == FindingStatus.INSUFFICIENT_DATA
    assert "2025-Q2" in f.missing


@pytest.mark.parametrize("field", ["total_current_asset", "current_liabilities", "total_equity",
                                   "total_assets", "total_liabilities"])
def test_null_balance_field(field):
    f = rule.evaluate(make_input({0: {field: None}}))
    assert f.status == FindingStatus.INSUFFICIENT_DATA
    assert field in f.missing


@pytest.mark.parametrize("field", ["total_assets", "total_liabilities"])
def test_zero_denominator(field):
    f = rule.evaluate(make_input({0: {field: 0.0}}))
    assert f.status == FindingStatus.INSUFFICIENT_DATA


def test_missing_quarter_within_ttm():
    f = rule.evaluate(make_input(drop=[3]))
    assert f.status == FindingStatus.INSUFFICIENT_DATA


def test_t4_not_required():
    assert rule.evaluate(make_input(drop=[4])).status != FindingStatus.INSUFFICIENT_DATA
