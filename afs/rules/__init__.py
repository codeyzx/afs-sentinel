"""The six Forensic Rules (docs/system-rules.md §3), in spec order."""

from __future__ import annotations

from afs.domain import EvaluationInput, FindingStatus, ForensicRule, RuleFinding
from afs.rules.altman import AltmanZAdapted
from afs.rules.beneish import BeneishAdapted
from afs.rules.dividend import EarningsWithoutDividend
from afs.rules.divergence import EarningsCashDivergence
from afs.rules.insider import InsiderSelling
from afs.rules.sloan import SloanAccrual

ALL_RULES: list[ForensicRule] = [
    SloanAccrual(),
    EarningsCashDivergence(),
    AltmanZAdapted(),
    BeneishAdapted(),
    InsiderSelling(),
    EarningsWithoutDividend(),
]

_BY_ID = {rule.rule_id: rule for rule in ALL_RULES}


def get_rule(rule_id: str) -> ForensicRule:
    return _BY_ID[rule_id]


def evaluate_all(inp: EvaluationInput) -> list[RuleFinding]:
    """Evaluate every rule; never raises — a crashing rule becomes INSUFFICIENT_DATA."""
    findings: list[RuleFinding] = []
    for rule in ALL_RULES:
        try:
            findings.append(rule.evaluate(inp))
        except Exception as exc:  # noqa: BLE001 - one broken rule must not stop the Audit Run
            missing = f"Kesalahan internal: {exc}"
            findings.append(
                RuleFinding(
                    rule_id=rule.rule_id,
                    status=FindingStatus.INSUFFICIENT_DATA,
                    value=None,
                    thresholds={},
                    inputs={},
                    headline=f"Tak bisa dinilai: {missing}",
                    missing=missing,
                )
            )
    return findings


__all__ = ["ALL_RULES", "get_rule", "evaluate_all"]
