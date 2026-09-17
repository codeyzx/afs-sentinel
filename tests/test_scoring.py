import pytest

from afs.domain import FindingStatus, RuleFinding, Severity
from afs.scoring import compute_score, severity_from_score

S, W, R, I = FindingStatus.PASS, FindingStatus.WARNING, FindingStatus.RED_FLAG, FindingStatus.INSUFFICIENT_DATA
IDS = [
    "SLOAN_ACCRUAL",
    "EARNINGS_CASH_DIVERGENCE",
    "ALTMAN_Z_ADAPTED",
    "BENEISH_ADAPTED",
    "INSIDER_SELLING",
    "EARNINGS_WITHOUT_DIVIDEND",
]


def findings(*statuses):
    return [RuleFinding(rid, st, None, {}, {}, "") for rid, st in zip(IDS, statuses)]


@pytest.mark.parametrize(
    "score,expected",
    [(0, Severity.LOW), (29.9, Severity.LOW), (30.0, Severity.MODERATE), (59.9, Severity.MODERATE),
     (60.0, Severity.CRITICAL), (100, Severity.CRITICAL)],
)
def test_severity_bands(score, expected):
    assert severity_from_score(score) == expected


def test_worked_example_4_3():
    r = compute_score(findings(R, R, W, W, I, S))
    assert r.evaluated_weight == 90
    assert r.score == 75.0
    assert r.severity == Severity.CRITICAL
    assert r.low_confidence is False
    assert r.severity_reason is None


def test_all_pass():
    r = compute_score(findings(S, S, S, S, S, S))
    assert r.score == 0.0 and r.severity == Severity.LOW and r.severity_reason is None


def test_all_insufficient_no_score():
    r = compute_score(findings(I, I, I, I, I, I))
    assert r.score is None and r.severity is None and r.evaluated_weight == 0


def test_rounding_one_decimal():
    # Insider WARNING (5 points) over evaluated weight 95 -> 5.263 -> 5.3
    r = compute_score(findings(S, S, S, S, W, I))
    assert r.score == round(100 * 5 / 95, 1) == 5.3


def test_core_floor_raises_low_to_moderate():
    r = compute_score(findings(S, S, R, S, S, S))  # 20/100 = 20 -> LOW
    assert r.score == 20.0
    assert r.severity == Severity.MODERATE
    assert r.severity_reason == "Minimal Sedang karena Altman Z'' (Adapted) berstatus Bahaya"


def test_floor_not_applied_for_non_core():
    r = compute_score(findings(S, S, S, R, S, S))
    assert r.severity == Severity.LOW and r.severity_reason is None


def test_floor_not_needed_when_already_moderate():
    r = compute_score(findings(R, W, S, S, S, S))  # 37.5
    assert r.severity == Severity.MODERATE and r.severity_reason is None


def test_low_confidence_boundary():
    # evaluated weight exactly 50 (Sloan + Divergence) -> not low confidence
    assert compute_score(findings(S, S, I, I, I, I)).low_confidence is False
    # 45 (Sloan + Altman) -> low confidence
    assert compute_score(findings(S, I, S, I, I, I)).low_confidence is True


def test_low_confidence_cap():
    r = compute_score(findings(I, I, R, R, I, I))  # weight 35, score 100
    assert r.score == 100.0
    assert r.low_confidence is True
    assert r.severity == Severity.MODERATE
    assert r.severity_reason == "Maksimal Sedang karena keyakinan rendah (bobot terevaluasi 35 dari 100)"


def test_low_confidence_moderate_not_capped():
    r = compute_score(findings(I, I, W, W, I, I))  # 50
    assert r.severity == Severity.MODERATE and r.severity_reason is None


def test_floor_for_sloan():
    r = compute_score(findings(R, S, S, S, S, S))  # 25 -> LOW -> floor
    assert r.severity == Severity.MODERATE
    assert r.severity_reason == "Minimal Sedang karena Sloan Accrual Ratio berstatus Bahaya"
