import json
from datetime import date, datetime

import pytest

from afs.domain import Filing, FindingStatus
from afs.rules.insider import InsiderSelling, classify
from tests.fixtures.rules_factory import make_input

rule = InsiderSelling()
AS_OF = date(2025, 11, 15)


def filing(day: date, kind: str = "sell", pct: float | None = 1.0, holder_type: str = "insider") -> Filing:
    return Filing(
        timestamp=datetime(day.year, day.month, day.day, 9, 0),
        transaction_type=kind,
        holder_type=holder_type,
        holder_name="PT Contoh Holding",
        share_percentage_transaction=pct,
        amount_transaction=1000.0,
        price=500.0,
    )


@pytest.mark.parametrize(
    "net,expected",
    [
        (2.0, FindingStatus.RED_FLAG),
        (1.99, FindingStatus.WARNING),
        (0.5, FindingStatus.WARNING),
        (0.49, FindingStatus.PASS),
        (-3.0, FindingStatus.PASS),
    ],
)
def test_classify_boundaries(net, expected):
    assert classify(net) == expected


def test_backtest_always_insufficient():
    f = rule.evaluate(make_input(filings=[filing(AS_OF, pct=10)], is_backtest=True))
    assert f.status == FindingStatus.INSUFFICIENT_DATA
    assert f.missing


def test_filings_none_insufficient():
    f = rule.evaluate(make_input(filings=None))
    assert f.status == FindingStatus.INSUFFICIENT_DATA
    assert f.headline.startswith("Tak bisa dinilai: ")


def test_empty_filings_pass():
    f = rule.evaluate(make_input(filings=[]))
    assert f.status == FindingStatus.PASS
    assert f.value == 0
    assert "Tidak ada" in f.headline


def test_red_flag_headline_example():
    f = rule.evaluate(make_input(as_of=AS_OF, filings=[filing(date(2025, 10, 1), pct=4.9)]))
    assert f.status == FindingStatus.RED_FLAG
    assert f.value == pytest.approx(4.9)
    assert f.headline == "Orang dalam/pemegang saham utama menjual bersih 4,9% saham dalam 90 hari terakhir."
    row = f.inputs["filings"][0]
    assert row["holder_name"] == "PT Contoh Holding" and row["type"] == "sell" and row["pct"] == 4.9
    assert "≥5%" in f.inputs["note"]
    json.dumps(f.to_dict())


def test_net_of_buys_and_boundary():
    filings = [filing(date(2025, 10, 1), "sell", 2.5), filing(date(2025, 10, 2), "buy", 0.5)]
    f = rule.evaluate(make_input(as_of=AS_OF, filings=filings))
    assert f.value == pytest.approx(2.0)
    assert f.status == FindingStatus.RED_FLAG


def test_others_ignored_but_listed_and_none_pct_is_zero():
    filings = [
        filing(date(2025, 10, 1), "others", 9.0),
        filing(date(2025, 10, 1), "sell", None),
        filing(date(2025, 10, 1), "sell", 0.5),
    ]
    f = rule.evaluate(make_input(as_of=AS_OF, filings=filings))
    assert f.value == pytest.approx(0.5)
    assert f.status == FindingStatus.WARNING
    assert len(f.inputs["filings"]) == 3
    assert [r["counted"] for r in f.inputs["filings"]].count(False) == 1


def test_non_insider_holder_type_excluded():
    f = rule.evaluate(make_input(as_of=AS_OF, filings=[filing(date(2025, 10, 1), pct=5.0, holder_type="institution")]))
    assert f.value == 0
    assert f.inputs["filings"] == []


def test_window_boundaries():
    # window is (as_of - 90d, as_of]: 2025-08-17 excluded, 2025-08-18 included, as_of included, after excluded
    filings = [
        filing(date(2025, 8, 17), pct=10.0),
        filing(date(2025, 8, 18), pct=0.25),
        filing(AS_OF, pct=0.25),
        filing(date(2025, 11, 16), pct=10.0),
    ]
    f = rule.evaluate(make_input(as_of=AS_OF, filings=filings))
    assert f.value == pytest.approx(0.5)
    assert f.status == FindingStatus.WARNING
