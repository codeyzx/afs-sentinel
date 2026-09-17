import json

import pytest

from afs.domain import FindingStatus
from afs.rules.divergence import EarningsCashDivergence, classify
from tests.fixtures.rules_factory import make_input

rule = EarningsCashDivergence()


@pytest.mark.parametrize(
    "de,do,expected",
    [
        (0.25, -0.15, FindingStatus.RED_FLAG),
        (0.2499, -0.15, FindingStatus.WARNING),
        (0.25, -0.1499, FindingStatus.WARNING),
        (0.10, 0.0, FindingStatus.WARNING),
        (0.0999, 0.0, FindingStatus.PASS),
        (0.10, 0.0001, FindingStatus.PASS),
        (-0.5, -0.9, FindingStatus.PASS),
    ],
)
def test_classify_boundaries(de, do, expected):
    assert classify(de, do) == expected


def _inp(e_t, e_t4, o_t, o_t4):
    return make_input(
        {0: {"earnings": e_t, "operating_cash_flow": o_t}, 4: {"earnings": e_t4, "operating_cash_flow": o_t4}}
    )


def test_red_flag_exact_boundary_from_data():
    f = rule.evaluate(_inp(125.0, 100.0, 85.0, 100.0))
    assert f.status == FindingStatus.RED_FLAG
    assert f.value == pytest.approx(0.25)
    assert f.inputs["delta_operating_cash_flow"] == pytest.approx(-0.15)
    json.dumps(f.to_dict())


def test_headline_example():
    f = rule.evaluate(_inp(152.0, 100.0, 72.0, 100.0))
    assert f.headline == "Laba naik 52% dibanding kuartal yang sama tahun lalu, tapi kas operasi turun 28%."


def test_warning_with_flat_ocf():
    f = rule.evaluate(_inp(110.0, 100.0, 100.0, 100.0))
    assert f.status == FindingStatus.WARNING


def test_negative_ocf_base_uses_absolute_value():
    # OCF -100 -> -150: Δ = -50/100 = -50%
    f = rule.evaluate(_inp(130.0, 100.0, -150.0, -100.0))
    assert f.inputs["delta_operating_cash_flow"] == pytest.approx(-0.5)
    assert f.status == FindingStatus.RED_FLAG


def test_pass_headline():
    f = rule.evaluate(_inp(100.0, 100.0, 120.0, 100.0))
    assert f.status == FindingStatus.PASS
    assert "kas operasi naik 20%" in f.headline


@pytest.mark.parametrize("base", [0.0, -10.0])
def test_non_positive_earnings_base_insufficient(base):
    f = rule.evaluate(_inp(100.0, base, 100.0, 100.0))
    assert f.status == FindingStatus.INSUFFICIENT_DATA
    assert f.missing


def test_zero_ocf_base_insufficient():
    f = rule.evaluate(_inp(150.0, 100.0, 100.0, 0.0))
    assert f.status == FindingStatus.INSUFFICIENT_DATA


@pytest.mark.parametrize("k", [4])
def test_missing_quarter(k):
    f = rule.evaluate(make_input(drop=[k]))
    assert f.status == FindingStatus.INSUFFICIENT_DATA
    assert "2024-Q3" in f.missing


def test_null_earnings():
    f = rule.evaluate(make_input({0: {"earnings": None}}))
    assert f.status == FindingStatus.INSUFFICIENT_DATA


def test_does_not_need_middle_quarters():
    f = rule.evaluate(make_input(drop=[1, 2, 3]))
    assert f.status != FindingStatus.INSUFFICIENT_DATA
