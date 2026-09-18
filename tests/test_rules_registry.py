import json
from datetime import date
from pathlib import Path

import pytest

from afs.domain import Dividend, EvaluationInput, FindingStatus, Quarter, RuleFinding
from afs.labels import RULE_META
from afs.rules import ALL_RULES, evaluate_all, get_rule
from tests.fixtures.rules_factory import make_input

SAMPLE_DIR = Path(__file__).resolve().parent.parent / ".scratch" / "api-verification"


def test_all_rules_spec_order_and_meta():
    assert [r.rule_id for r in ALL_RULES] == list(RULE_META)
    for r in ALL_RULES:
        meta = RULE_META[r.rule_id]
        assert (r.name, r.subtitle, r.weight, r.is_core) == (meta.name, meta.subtitle, meta.weight, meta.is_core)


def test_get_rule():
    assert get_rule("ALTMAN_Z_ADAPTED").rule_id == "ALTMAN_Z_ADAPTED"
    with pytest.raises(KeyError):
        get_rule("NOPE")


def test_evaluate_all_returns_six_serialisable_findings():
    findings = evaluate_all(make_input())
    assert [f.rule_id for f in findings] == list(RULE_META)
    for f in findings:
        d = json.loads(json.dumps(f.to_dict()))
        assert RuleFinding.from_dict(d).status == f.status
        assert {"values", "formula", "endpoint"} <= set(f.inputs)


def test_evaluate_all_never_raises(monkeypatch):
    class Boom:
        rule_id = "SLOAN_ACCRUAL"

        def evaluate(self, inp):
            raise ValueError("pembagian gagal")

    import afs.rules as rules_pkg

    monkeypatch.setattr(rules_pkg, "ALL_RULES", [Boom(), *rules_pkg.ALL_RULES[1:]])
    findings = evaluate_all(make_input())
    assert len(findings) == 6
    f = findings[0]
    assert f.status == FindingStatus.INSUFFICIENT_DATA
    assert f.missing == "Kesalahan internal: pembagian gagal"
    assert f.headline == "Tak bisa dinilai: Kesalahan internal: pembagian gagal"
    assert findings[1].status != FindingStatus.INSUFFICIENT_DATA


def test_insufficient_findings_have_missing_and_headline():
    findings = evaluate_all(make_input(drop=[1, 2, 3, 4], filings=None, dividends=None))
    for f in findings:
        assert f.status == FindingStatus.INSUFFICIENT_DATA
        assert f.missing
        assert f.headline == f"Tak bisa dinilai: {f.missing}"


def test_realism_asii_sample():
    path = SAMPLE_DIR / "asii_q.json"
    if not path.exists():
        pytest.skip("API sample not available")
    rows = sorted(json.loads(path.read_text()), key=lambda r: r["date"], reverse=True)
    if len(rows) < 5:
        pytest.skip("need 5 quarters")
    quarters = [Quarter(report_date=date.fromisoformat(r["date"]), data=r) for r in rows[:5]]
    dividends: list[Dividend] = []
    ca_path = SAMPLE_DIR / "corporate_actions_ASII.json"
    if ca_path.exists():
        ca = json.loads(ca_path.read_text()).get("corporate_actions") or {}
        dividends = [
            Dividend(date.fromisoformat(d["ex_date"]), d.get("dividend_amount"))
            for d in (ca.get("dividend") or [])
            if d.get("ex_date")
        ]
    inp = EvaluationInput(
        symbol="ASII", quarters=quarters, as_of=date(2026, 9, 18), filings=[], dividends=dividends
    )
    findings = evaluate_all(inp)
    for f in findings:
        assert not (f.missing or "").startswith("Kesalahan internal"), f.missing
        assert f.status != FindingStatus.INSUFFICIENT_DATA, (f.rule_id, f.missing)
        json.dumps(f.to_dict())


def test_rule_dots_keep_six_fixed_numbered_positions():
    """Dot N is always rule N, whatever the findings contain — the number is a position, not a rank."""
    from afs.web.queries import rule_dots, rule_legend

    partial = [{"rule_id": "ALTMAN_Z_ADAPTED", "status": "RED_FLAG", "headline": "x"}]
    dots = rule_dots(partial)

    assert [d["number"] for d in dots] == [1, 2, 3, 4, 5, 6]
    assert [d["rule_id"] for d in dots] == list(RULE_META)
    third = dots[2]
    assert third["rule_id"] == "ALTMAN_Z_ADAPTED" and third["tone"] == "red"
    # Rules with no finding keep their slot rather than collapsing the row.
    assert dots[0]["tone"] == "gray" and dots[0]["label"] == "Belum dinilai"

    # The legend numbers must agree with the dot numbers, or the legend lies.
    assert [m["number"] for m in rule_legend()] == [d["number"] for d in dots]
    assert [m["rule_id"] for m in rule_legend()] == [d["rule_id"] for d in dots]
