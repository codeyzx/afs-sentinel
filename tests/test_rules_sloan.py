import json

import pytest

from afs.domain import FindingStatus
from afs.rules.sloan import SloanAccrual, classify
from tests.fixtures.rules_factory import make_input

rule = SloanAccrual()


def test_meta_from_labels():
    assert rule.rule_id == "SLOAN_ACCRUAL"
    assert rule.weight == 25 and rule.is_core
    assert rule.name == "Sloan Accrual Ratio"


@pytest.mark.parametrize(
    "ratio,expected",
    [
        (0.10, FindingStatus.WARNING),
        (0.1000001, FindingStatus.RED_FLAG),
        (0.05, FindingStatus.PASS),
        (0.0500001, FindingStatus.WARNING),
        (-0.2, FindingStatus.PASS),
    ],
)
def test_classify_boundaries(ratio, expected):
    assert classify(ratio) == expected


def test_red_flag_value_and_headline():
    # TTM earnings 4*150=600, TTM OCF 4*81=324, diff 276, avg assets 2000 -> 13.8%
    inp = make_input({k: {"earnings": 150.0, "operating_cash_flow": 81.0} for k in range(4)})
    f = rule.evaluate(inp)
    assert f.status == FindingStatus.RED_FLAG
    assert f.value == pytest.approx(0.138)
    assert f.headline == "13,8% dari aset tercatat sebagai laba yang belum menjadi uang tunai (batas wajar 10%)."
    json.dumps(f.to_dict())
    assert f.to_dict()["inputs"]["endpoint"] == "/v2/financials/quarterly/TEST/"
    assert len(f.inputs["values"]) == 10


def test_exact_boundary_via_data_is_warning():
    # diff 4*50=200, avg assets 2000 -> exactly 10%
    inp = make_input({k: {"earnings": 150.0, "operating_cash_flow": 100.0} for k in range(4)})
    f = rule.evaluate(inp)
    assert f.value == pytest.approx(0.10)
    assert f.status == FindingStatus.WARNING


def test_pass_when_cash_exceeds_earnings():
    f = rule.evaluate(make_input({k: {"operating_cash_flow": 200.0} for k in range(4)}))
    assert f.status == FindingStatus.PASS
    assert f.value < 0


@pytest.mark.parametrize("k", [1, 4])
def test_missing_quarter_insufficient(k):
    f = rule.evaluate(make_input(drop=[k]))
    assert f.status == FindingStatus.INSUFFICIENT_DATA
    assert f.value is None
    assert "tidak tersedia" in f.missing
    assert f.headline.startswith("Tak bisa dinilai: ")


@pytest.mark.parametrize("field", ["earnings", "operating_cash_flow", "total_assets"])
def test_null_field_insufficient(field):
    f = rule.evaluate(make_input({0: {field: None}}))
    assert f.status == FindingStatus.INSUFFICIENT_DATA
    assert field in f.missing


def test_zero_assets_insufficient():
    f = rule.evaluate(make_input({0: {"total_assets": 0.0}, 4: {"total_assets": 0.0}}))
    assert f.status == FindingStatus.INSUFFICIENT_DATA
