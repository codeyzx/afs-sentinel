import json

import pytest

from afs.domain import FindingStatus
from afs.rules.beneish import BeneishAdapted, classify
from tests.fixtures.rules_factory import make_input

rule = BeneishAdapted()


@pytest.mark.parametrize(
    "exceeded,evaluated,expected",
    [
        (0, 1, FindingStatus.INSUFFICIENT_DATA),
        (1, 1, FindingStatus.INSUFFICIENT_DATA),
        (0, 2, FindingStatus.PASS),
        (1, 2, FindingStatus.WARNING),
        (2, 2, FindingStatus.RED_FLAG),
        (3, 3, FindingStatus.RED_FLAG),
    ],
)
def test_classify(exceeded, evaluated, expected):
    assert classify(exceeded, evaluated) == expected


def test_pass_base_case():
    f = rule.evaluate(make_input())
    assert f.status == FindingStatus.PASS
    assert f.value == 0
    assert f.headline == "0 dari 3 indikator tekanan manipulasi menyala."
    assert set(f.inputs["sub_indices"]) == {"GMI", "SGI", "LVGI"}
    assert "3 dari 8" in f.inputs["note"]
    json.dumps(f.to_dict())


def test_sgi_boundary():
    # revenue_t4 = 1000; t = 1610 -> SGI exactly 1.61 (not exceeded); keep gross margin constant
    at = rule.evaluate(make_input({0: {"revenue": 1610.0, "gross_profit": 483.0}}))
    assert at.inputs["sub_indices"]["SGI"]["value"] == pytest.approx(1.61)
    assert at.status == FindingStatus.PASS
    above = rule.evaluate(make_input({0: {"revenue": 1620.0, "gross_profit": 486.0}}))
    assert above.status == FindingStatus.WARNING
    assert above.headline == "1 dari 3 indikator tekanan manipulasi menyala: penjualan tumbuh sangat cepat."


def test_gmi_boundary():
    # margin t-4 = 0.3; GMI = 0.3 / margin_t; margin_t = 0.3/1.19 -> exactly boundary
    gp_equal = 1000.0 * 0.3 / 1.19
    at = rule.evaluate(make_input({0: {"gross_profit": gp_equal}}))
    assert at.inputs["sub_indices"]["GMI"]["value"] == pytest.approx(1.19)
    above = rule.evaluate(make_input({0: {"gross_profit": 200.0}}))  # GMI = 1.5
    assert above.inputs["sub_indices"]["GMI"]["exceeded"] is True
    assert above.status == FindingStatus.WARNING


def test_lvgi_boundary():
    # leverage t-4 = 0.4; t = 0.444 -> 1.11
    at = rule.evaluate(make_input({0: {"total_liabilities": 888.0}}))
    assert at.inputs["sub_indices"]["LVGI"]["value"] == pytest.approx(1.11)
    assert at.inputs["sub_indices"]["LVGI"]["exceeded"] is False
    above = rule.evaluate(make_input({0: {"total_liabilities": 890.0}}))
    assert above.inputs["sub_indices"]["LVGI"]["exceeded"] is True


def test_red_flag_headline_example():
    f = rule.evaluate(make_input({0: {"gross_profit": 200.0, "total_liabilities": 1000.0}}))
    assert f.status == FindingStatus.RED_FLAG
    assert f.value == 2
    assert f.headline == "2 dari 3 indikator tekanan manipulasi menyala: margin kotor memburuk dan utang melonjak."


def test_two_evaluable_is_enough():
    f = rule.evaluate(make_input({0: {"gross_profit": None}}))
    assert f.status == FindingStatus.PASS
    assert f.inputs["sub_indices"]["GMI"]["evaluated"] is False
    assert f.headline.startswith("0 dari 2 ")


def test_non_positive_denominator_not_evaluated():
    f = rule.evaluate(make_input({4: {"revenue": 0.0}}))  # GMI and SGI not evaluated
    assert f.status == FindingStatus.INSUFFICIENT_DATA
    assert "GMI" in f.missing and "SGI" in f.missing


def test_missing_t4_insufficient():
    f = rule.evaluate(make_input(drop=[4]))
    assert f.status == FindingStatus.INSUFFICIENT_DATA
    assert "2024-Q3" in f.missing
