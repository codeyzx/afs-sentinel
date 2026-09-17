"""Composite Risk Score and Incident Severity — docs/system-rules.md §4.1–4.2."""

from __future__ import annotations

from typing import Sequence

from afs.domain import FindingStatus, RuleFinding, ScoreResult, Severity
from afs.labels import CORE_RULE_IDS, FINDING_LABEL, RULE_META, SEVERITY_LABEL

STATUS_FACTOR = {FindingStatus.RED_FLAG: 1.0, FindingStatus.WARNING: 0.5, FindingStatus.PASS: 0.0}
MODERATE_FROM = 30.0
CRITICAL_FROM = 60.0
LOW_CONFIDENCE_BELOW = 50.0
TOTAL_WEIGHT = sum(m.weight for m in RULE_META.values())


def severity_from_score(score: float) -> Severity:
    if score >= CRITICAL_FROM:
        return Severity.CRITICAL
    if score >= MODERATE_FROM:
        return Severity.MODERATE
    return Severity.LOW


def _fmt_weight(w: float) -> str:
    return str(int(w)) if float(w).is_integer() else f"{w:.1f}".replace(".", ",")


def compute_score(findings: Sequence[RuleFinding]) -> ScoreResult:
    points = 0.0
    evaluated_weight = 0.0
    for f in findings:
        if f.status == FindingStatus.INSUFFICIENT_DATA:
            continue
        weight = RULE_META[f.rule_id].weight
        evaluated_weight += weight
        points += weight * STATUS_FACTOR[f.status]

    low_confidence = evaluated_weight < LOW_CONFIDENCE_BELOW
    if evaluated_weight == 0:
        return ScoreResult(score=None, severity=None, low_confidence=True, evaluated_weight=0.0)

    score = round(100 * points / evaluated_weight, 1)
    severity = severity_from_score(score)
    reasons: list[str] = []

    red_core = [
        f.rule_id for f in findings if f.rule_id in CORE_RULE_IDS and f.status == FindingStatus.RED_FLAG
    ]
    if red_core and severity == Severity.LOW:
        severity = Severity.MODERATE
        names = " dan ".join(RULE_META[r].name for r in red_core)
        reasons.append(
            f"Minimal {SEVERITY_LABEL[Severity.MODERATE]} karena {names} "
            f"berstatus {FINDING_LABEL[FindingStatus.RED_FLAG]}"
        )

    if low_confidence and severity == Severity.CRITICAL:
        severity = Severity.MODERATE
        reasons.append(
            f"Maksimal {SEVERITY_LABEL[Severity.MODERATE]} karena keyakinan rendah "
            f"(bobot terevaluasi {_fmt_weight(evaluated_weight)} dari {_fmt_weight(TOTAL_WEIGHT)})"
        )

    return ScoreResult(
        score=score,
        severity=severity,
        low_confidence=low_confidence,
        evaluated_weight=evaluated_weight,
        severity_reason="; ".join(reasons) if reasons else None,
    )
